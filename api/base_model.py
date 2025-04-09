"""
Base Model Module

This module defines the BaseModel abstract class that all model implementations 
must inherit from. It provides the foundation for integrating different 
language models into the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator


class BaseModel(ABC):
    """
    Abstract base class for all language models in the system.
    
    All model implementations must inherit from this class and implement
    its abstract methods.
    """
    
    def __init__(self, 
                 model_id: str, 
                 name: str, 
                 description: str = "",
                 architecture: Optional[str] = None,
                 parameters: Optional[str] = None, # e.g., "7B", "13B"
                 context_length: Optional[int] = None,
                 quantization: Optional[str] = None, # e.g., "Q4_K_M", "FP16"
                 supports_tools: bool = False,
                 supports_vision: bool = False,
                 is_embedding_model: bool = False,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize a new model instance.
        
        Args:
            model_id: Unique identifier for this model (e.g., "llama3:8b-instruct-q5_K_M")
            name: Display name of the model (e.g., "Llama 3 8B Instruct Q5")
            description: Description of the model's capabilities or origin
            architecture: Model architecture (e.g., "llama", "mistral")
            parameters: Number of parameters (e.g., "8B")
            context_length: Maximum context length in tokens
            quantization: Quantization level applied to the model
            supports_tools: Whether the model inherently supports tool calling
            supports_vision: Whether the model inherently supports vision (multimodal) input
            is_embedding_model: Whether this model is primarily for generating embeddings
            config: Additional configuration parameters for this model
        """
        if not model_id or not name:
            raise ValueError("model_id and name are required.")
            
        self.model_id = model_id
        self.name = name
        self.description = description
        self.architecture = architecture
        self.parameters = parameters
        self.context_length = context_length
        self.quantization = quantization
        self.supports_tools = supports_tools
        self.supports_vision = supports_vision
        self.is_embedding_model = is_embedding_model
        self.config = config or {}
        self._is_loaded = False

    @abstractmethod
    async def load(self) -> bool:
        """
        Load the model into memory. This might involve downloading weights, 
        allocating GPU resources, etc.
        
        Returns:
            True if loading was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def unload(self) -> None:
        """
        Unload the model from memory and release resources.
        """
        pass

    @abstractmethod
    async def generate(self, prompt: str, 
                       options: Optional[Dict[str, Any]] = None,
                       tools: Optional[List[Dict[str, Any]]] = None,
                       images: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a response based on the prompt and options.
        
        Args:
            prompt: The input prompt string.
            options: Generation parameters (e.g., temperature, top_p).
            tools: Optional list of tools for the model to use (if supported).
            images: Optional list of base64 encoded images (if supported).
            
        Returns:
            A dictionary containing the generated response and potentially other metadata. 
            Expected keys might include 'response', 'tool_calls', 'done', etc.
        """
        pass

    @abstractmethod
    async def generate_stream(self, prompt: str, 
                              options: Optional[Dict[str, Any]] = None,
                              tools: Optional[List[Dict[str, Any]]] = None,
                              images: Optional[List[str]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a response as a stream of chunks.
        
        Args:
            prompt: The input prompt string.
            options: Generation parameters.
            tools: Optional list of tools.
            images: Optional list of base64 encoded images.
            
        Returns:
            An async generator yielding response chunks (dictionaries).
            Each chunk might contain keys like 'response' (partial text), 
            'tool_calls', 'done', etc.
        """
        raise NotImplementedError("Streaming generation not implemented for this model.")
        yield {} # Must yield at least once for async generator typing

    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text. Only applicable if is_embedding_model is True.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
            
        Raises:
            NotImplementedError if the model does not support embedding generation.
        """
        if not self.is_embedding_model:
            raise NotImplementedError(f"Model '{self.model_id}' does not support embedding generation.")
        # Default implementation raises error; subclasses should override if they support embeddings.
        raise NotImplementedError("Embedding generation not implemented for this specific model class.")

    def is_loaded(self) -> bool:
        """Check if the model is currently loaded."""
        return self._is_loaded

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get the model's static metadata.
        
        Returns:
            A dictionary containing the model's metadata.
        """
        return {
            "id": self.model_id,
            "name": self.name,
            "description": self.description,
            "architecture": self.architecture,
            "parameters": self.parameters,
            "context_length": self.context_length,
            "quantization": self.quantization,
            "supports_tools": self.supports_tools,
            "supports_vision": self.supports_vision,
            "is_embedding_model": self.is_embedding_model,
            "config": self.config,
            "is_loaded": self.is_loaded() 
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(model_id='{self.model_id}', name='{self.name}')>"
