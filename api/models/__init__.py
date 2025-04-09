"""
Models Package

This package provides functionality for working with different language models.
It includes a registry for managing model instances and implementations for
specific model types.
"""

from typing import Dict, List, Optional, Any
import asyncio
import os
import sys

# Add the parent directory to the sys.path to make imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.base_model import BaseModel
except ImportError:
    # Try relative import if absolute import fails
    from ..base_model import BaseModel

from api.models.ollama_model import OllamaModel
from logger import app_logger

# Default models for testing if no models are available
DEFAULT_TEST_MODELS = [
    {
        "name": "llama3.2",
        "id": "llama3.2",
        "description": "Open source LLM from Meta (default model)",
        "architecture": "llama",
        "parameters": "3.2B",
        "context_length": 131072,
        "quantization": "Q4_K_M",
        "supports_tools": True,
        "supports_vision": True,
        "is_embedding_model": False
    },
    {
        "name": "nomic-embed-text",
        "id": "nomic-embed-text",
        "description": "Embedding model for text",
        "architecture": "nomic",
        "parameters": "None",
        "context_length": 8192,
        "quantization": "F16",
        "supports_tools": False,
        "supports_vision": False,
        "is_embedding_model": True
    }
]

class ModelRegistry:
    """
    Registry for managing language model instances.
    
    Provides methods to load, unload, and access language models.
    """
    
    def __init__(self):
        """Initialize the model registry."""
        self._models: Dict[str, BaseModel] = {}
        self._lock = asyncio.Lock()
    
    async def get_model(self, model_id: str) -> Optional[BaseModel]:
        """
        Get a model instance by ID, loading it if necessary.
        
        Args:
            model_id: The ID of the model to get
            
        Returns:
            The model instance, or None if it couldn't be loaded
        """
        # Check if model already exists
        if model_id in self._models:
            return self._models[model_id]
        
        # Lock to prevent race conditions when creating new models
        async with self._lock:
            # Check again inside the lock
            if model_id in self._models:
                return self._models[model_id]
            
            # Create a new model instance
            try:
                # Currently only Ollama models are supported
                model = OllamaModel(model_id=model_id)
                self._models[model_id] = model
                
                # Try to load the model, but don't fail if loading fails
                try:
                    await model.load()
                except Exception as e:
                    app_logger.warning(f"Failed to load model {model_id}: {str(e)}")
                
                return model
            except Exception as e:
                app_logger.error(f"Error creating model instance for {model_id}: {str(e)}")
                return None
    
    async def initialize_model(self, model_id: str) -> bool:
        """
        Initialize a model with the specified ID.
        
        Args:
            model_id: The ID of the model to initialize
            
        Returns:
            True if initialization was successful, False otherwise
        """
        model = await self.get_model(model_id)
        if not model:
            return False
        
        return await model.load()
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload a model from memory.
        
        Args:
            model_id: The ID of the model to unload
            
        Returns:
            True if unloading was successful, False otherwise
        """
        if model_id not in self._models:
            # Model not loaded, so consider it a success
            return True
        
        try:
            model = self._models[model_id]
            await model.unload()
            return True
        except Exception as e:
            app_logger.error(f"Error unloading model {model_id}: {str(e)}")
            return False
    
    async def get_all_models(self) -> List[Dict[str, Any]]:
        """
        Get metadata for all available models.
        
        Returns:
            List of dictionaries containing model metadata
        """
        # Get list of available models from Ollama
        try:
            import requests
            base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            
            try:
                response = requests.get(f"{base_url}/api/tags", timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    
                    # If no models are available, try using 'ollama list' command directly
                    if not models:
                        app_logger.info("No models found via API, trying CLI command")
                        import subprocess
                        try:
                            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
                            if result.returncode == 0 and result.stdout.strip():
                                # Parse the output to get model names
                                lines = result.stdout.strip().split('\n')
                                # Skip header if present
                                if lines and "NAME" in lines[0].upper():
                                    lines = lines[1:]
                                
                                for line in lines:
                                    if line.strip():
                                        # Split by whitespace and take the first part as model name
                                        parts = line.strip().split()
                                        if parts:
                                            model_id = parts[0]
                                            models.append({"name": model_id})
                        except Exception as cli_e:
                            app_logger.warning(f"Failed to get models via CLI: {str(cli_e)}")
                    
                    # Still no models? Use hardcoded defaults for testing
                    if not models:
                        app_logger.warning("No models available from API or CLI, using default test models")
                        return DEFAULT_TEST_MODELS
                    
                    # Convert to list of model metadata
                    result = []
                    for model_data in models:
                        model_id = model_data.get("name")
                        
                        # Check if we already have a model instance
                        if model_id in self._models:
                            # Use metadata from instance
                            model = self._models[model_id]
                            result.append(model.get_metadata())
                        else:
                            # Create a new instance to get full metadata
                            try:
                                model = OllamaModel(model_id=model_id)
                                result.append(model.get_metadata())
                            except Exception as model_e:
                                app_logger.warning(f"Failed to create model instance for {model_id}: {str(model_e)}")
                                # Use basic metadata as fallback
                                result.append({
                                    "id": model_id,
                                    "name": model_id,
                                    "description": "",
                                    "architecture": None,
                                    "parameters": None,
                                    "context_length": None,
                                    "quantization": None,
                                    "supports_tools": False,
                                    "supports_vision": False,
                                    "is_embedding_model": False,
                                    "is_loaded": False
                                })
                    
                    return result
                else:
                    app_logger.error(f"Error getting models from Ollama API: {response.status_code}")
            except requests.RequestException as req_e:
                app_logger.error(f"Request error getting models from Ollama: {str(req_e)}")
            
            # If we reach here, we couldn't get models from the API or CLI
            # Return default test models
            app_logger.warning("Returning default test models due to API/CLI failure")
            return DEFAULT_TEST_MODELS
                
        except Exception as e:
            app_logger.error(f"Error getting available models: {str(e)}")
            # Return default test models in case of any error
            return DEFAULT_TEST_MODELS
    
    async def cleanup(self) -> None:
        """Clean up all model instances."""
        # Unload all models
        for model_id, model in list(self._models.items()):
            try:
                await model.unload()
            except Exception as e:
                app_logger.error(f"Error unloading model {model_id}: {str(e)}")
        
        # Clear the registry
        self._models.clear()

# Create a global model registry instance
model_registry = ModelRegistry() 