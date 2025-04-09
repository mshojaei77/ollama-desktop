"""
Ollama Model Implementation

This module implements the BaseModel for Ollama models, providing methods
to load, unload, and generate text with Ollama models.
"""

import os
import json
import asyncio
import sys
import subprocess
from typing import Dict, List, Optional, Any, AsyncGenerator

# Add the parent directory to the sys.path to make imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from api.base_model import BaseModel
except ImportError:
    # Try relative import if absolute import fails
    from ..base_model import BaseModel

try:
    from logger import app_logger
except ImportError:
    import logging
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app_logger.addHandler(handler)

class OllamaModel(BaseModel):
    """
    Implementation of BaseModel for Ollama models.
    
    Provides functionality to interact with Ollama models, including loading,
    unloading, and generating text with or without tools.
    """
    
    def __init__(self, 
                 model_id: str,
                 name: Optional[str] = None,
                 description: str = "",
                 ollama_base_url: str = None):
        """
        Initialize a new Ollama model instance.
        
        Args:
            model_id: Unique identifier for the model in Ollama (e.g., "llama3")
            name: Display name of the model (defaults to model_id if not provided)
            description: Description of the model's capabilities
            ollama_base_url: Base URL for the Ollama API (defaults to env var or localhost)
        """
        # Get model details before initialization
        model_info = self._get_model_info(model_id, ollama_base_url)
        
        # Get model defaults based on name patterns
        defaults = self._get_model_defaults(model_id)
        
        # Merge defaults with actual info, using actual info when available
        for key, value in defaults.items():
            if key not in model_info or model_info[key] is None:
                model_info[key] = value
        
        super().__init__(
            model_id=model_id,
            name=name or model_id,
            description=description or model_info.get('description', ''),
            architecture=model_info.get('architecture'),
            parameters=model_info.get('parameters'),
            context_length=model_info.get('context_length'),
            quantization=model_info.get('quantization'),
            supports_tools=model_info.get('supports_tools', False),
            supports_vision=model_info.get('supports_vision', False),
            is_embedding_model=model_info.get('is_embedding_model', False)
        )
        
        self.ollama_base_url = ollama_base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self._import_ollama()
    
    def _get_model_defaults(self, model_id: str) -> Dict[str, Any]:
        """Get default parameter values based on model name patterns"""
        defaults = {
            'architecture': None,
            'parameters': None,
            'context_length': None,
            'quantization': None,
            'supports_tools': False,
            'supports_vision': False,
            'is_embedding_model': False,
            'description': ""
        }
        
        # Set specific model defaults based on name patterns
        model_id_lower = model_id.lower()
        
        # Llama 3 models
        if 'llama3' in model_id_lower:
            defaults['architecture'] = 'llama'
            defaults['context_length'] = 131072  # 128k context
            defaults['supports_tools'] = True
            defaults['description'] = "An open-source language model from Meta"
            
            # Extract parameter size if possible
            if '1b' in model_id_lower:
                defaults['parameters'] = '1B'
            elif '3.2' in model_id_lower or '3b' in model_id_lower:
                defaults['parameters'] = '3.2B'
            elif '8b' in model_id_lower:
                defaults['parameters'] = '8B'
            elif '70b' in model_id_lower:
                defaults['parameters'] = '70B'
            
            # Extract quantization
            if 'q4' in model_id_lower:
                defaults['quantization'] = 'Q4_K_M'
            elif 'q5' in model_id_lower:
                defaults['quantization'] = 'Q5_K_M'
            elif 'q6' in model_id_lower:
                defaults['quantization'] = 'Q6_K'
            elif 'q8' in model_id_lower:
                defaults['quantization'] = 'Q8_0'
            elif 'f16' in model_id_lower:
                defaults['quantization'] = 'F16'
        
        # Gemma models
        elif 'gemma' in model_id_lower:
            defaults['architecture'] = 'gemma'
            defaults['context_length'] = 8192
            
            # Extract parameter size if possible
            if '1b' in model_id_lower:
                defaults['parameters'] = '1B'
            elif '2b' in model_id_lower:
                defaults['parameters'] = '2B'
            elif '7b' in model_id_lower:
                defaults['parameters'] = '7B'
            elif '12b' in model_id_lower:
                defaults['parameters'] = '12B'
        
        # Qwen models
        elif 'qwen' in model_id_lower:
            defaults['architecture'] = 'qwen'
            defaults['context_length'] = 32768
            
            # Extract parameter size if possible
            if '0.5b' in model_id_lower:
                defaults['parameters'] = '0.5B'
            elif '1.5b' in model_id_lower:
                defaults['parameters'] = '1.5B'
            elif '7b' in model_id_lower:
                defaults['parameters'] = '7B'
            elif '14b' in model_id_lower:
                defaults['parameters'] = '14B'
        
        # Phi models
        elif 'phi' in model_id_lower:
            defaults['architecture'] = 'phi'
            defaults['context_length'] = 4096
            
            # Parse phi4-mini as 3.8B
            if 'mini' in model_id_lower:
                defaults['parameters'] = '3.8B'
        
        # Embedding models
        if any(embed_term in model_id_lower for embed_term in ['embed', 'nomic-embed', 'bge', 'arctic-embed']):
            defaults['is_embedding_model'] = True
            defaults['context_length'] = 8192
        
        # Vision models
        if any(vision_term in model_id_lower for vision_term in ['vision', 'llava', 'bakllava']):
            defaults['supports_vision'] = True
        
        return defaults
        
    def _import_ollama(self):
        """Import the Ollama Python client dynamically to support different versions."""
        try:
            import ollama
            self._ollama = ollama
            self._async_client = ollama.AsyncClient(host=self.ollama_base_url)
            app_logger.info("Successfully imported Ollama Python client")
        except ImportError:
            app_logger.warning("Ollama Python client not available, using requests fallback")
            self._ollama = None
            self._async_client = None
            import requests
            self._requests = requests
    
    def _get_model_info(self, model_id: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a model from Ollama.
        
        Args:
            model_id: The model identifier
            base_url: Optional base URL for the Ollama API
            
        Returns:
            Dictionary with model information
        """
        model_info = {
            'architecture': None,
            'parameters': None,
            'context_length': None,
            'quantization': None,
            'supports_tools': False,
            'supports_vision': False,
            'is_embedding_model': False,
            'description': ""
        }
        
        # Try to get model information from ollama CLI first (most reliable)
        try:
            # Run 'ollama show <model>' command with UTF-8 encoding
            cmd = ["ollama", "show", model_id]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=10)
            
            if result.returncode == 0:
                # Successfully got model info through CLI
                output = result.stdout
                
                # Parse architecture from CLI output
                if "Architecture:" in output:
                    arch_line = [line for line in output.split('\n') if "Architecture:" in line]
                    if arch_line:
                        model_info['architecture'] = arch_line[0].split("Architecture:")[1].strip()
                
                # Parse parameter count
                if "Parameters:" in output:
                    param_line = [line for line in output.split('\n') if "Parameters:" in line]
                    if param_line:
                        model_info['parameters'] = param_line[0].split("Parameters:")[1].strip()
                
                # Parse context length
                if "Context:" in output:
                    ctx_line = [line for line in output.split('\n') if "Context:" in line]
                    if ctx_line:
                        ctx_str = ctx_line[0].split("Context:")[1].strip()
                        try:
                            model_info['context_length'] = int(ctx_str)
                        except ValueError:
                            # Handle if it's not a clean integer
                            model_info['context_length'] = ctx_str
                
                # Parse quantization
                if "Quantization:" in output:
                    quant_line = [line for line in output.split('\n') if "Quantization:" in line]
                    if quant_line:
                        model_info['quantization'] = quant_line[0].split("Quantization:")[1].strip()
                
                # Check for model description
                desc_lines = []
                in_description = False
                for line in output.split('\n'):
                    if line.strip() == "Description:":
                        in_description = True
                        continue
                    if in_description and line.strip() and not line.startswith("---"):
                        desc_lines.append(line.strip())
                    elif in_description and (line.startswith("---") or not line.strip()):
                        break
                
                if desc_lines:
                    model_info['description'] = ' '.join(desc_lines)
                
                # Try to detect capabilities from model name and output
                model_info['supports_vision'] = any(model in model_id.lower() for model in 
                                                ['vision', 'llava', 'bakllava', 'moondream', 'cogvlm', 'llama3.2-vision'])
                
                model_info['is_embedding_model'] = any(model in model_id.lower() for model in 
                                                  ['embed', 'embedding', 'nomic-embed-text', 'mxbai-embed', 'all-minilm', 'bge'])
                
                model_info['supports_tools'] = 'llama3' in model_id.lower() or 'tool' in model_id.lower() or 'function' in output.lower()
                
                app_logger.info(f"Retrieved model info for {model_id} using CLI command")
                
                # Try to get additional info through the API as well
                try:
                    self._get_model_info_from_api(model_id, base_url, model_info)
                except Exception as api_e:
                    app_logger.warning(f"Could not get additional API model info: {str(api_e)}")
                
                return model_info
        except (subprocess.SubprocessError, FileNotFoundError, TimeoutError, UnicodeDecodeError) as e:
            app_logger.warning(f"Could not get model info using CLI: {str(e)}")
            # Fall back to API method if CLI fails
            pass
        
        # Fall back to the API method if CLI didn't work
        try:
            self._get_model_info_from_api(model_id, base_url, model_info)
        except Exception as e:
            app_logger.error(f"Error getting model info for {model_id}: {str(e)}")
        
        return model_info
    
    def _get_model_info_from_api(self, model_id: str, base_url: Optional[str] = None, model_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get model information using the Ollama API"""
        if model_info is None:
            model_info = {}
        
        import requests
        base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Try to get model information using 'show' endpoint
        response = requests.get(f"{base_url}/api/show?name={model_id}")
        
        if response.status_code == 200:
            data = response.json()
            model_details = data.get('model', {})
            
            # Extract relevant information if not already set by CLI
            if not model_info.get('architecture'):
                model_info['architecture'] = model_details.get('architecture')
            
            if not model_info.get('parameters'):
                model_info['parameters'] = model_details.get('parameters')
            
            if not model_info.get('context_length'):
                model_info['context_length'] = model_details.get('context', model_details.get('context_length'))
            
            if not model_info.get('quantization'):
                model_info['quantization'] = model_details.get('quantization')
            
            # Attempt to detect capabilities from template and parameters if not already set
            template = data.get('template', '')
            parameters = data.get('parameters', {})
            
            # Check for vision support if not already detected
            if not model_info.get('supports_vision', False):
                model_info['supports_vision'] = 'image' in template.lower() or any(model in model_id.lower() for model in 
                                                    ['vision', 'llava', 'bakllava', 'moondream', 'cogvlm', 'llama3.2-vision'])
            
            # Check for embedding support if not already detected
            if not model_info.get('is_embedding_model', False):
                model_info['is_embedding_model'] = any(model in model_id.lower() for model in 
                                                  ['embed', 'embedding', 'nomic-embed-text', 'mxbai-embed', 'all-minilm', 'bge'])
            
            # Check for tool support if not already detected
            if not model_info.get('supports_tools', False):
                model_info['supports_tools'] = 'llama3' in model_id.lower() or (
                    'function' in template.lower() or
                    'tool' in template.lower() or
                    any('tool' in str(param).lower() for param in parameters)
                )
            
            app_logger.info(f"Retrieved model info for {model_id} from API")
        else:
            app_logger.warning(f"Could not get model info for {model_id} from API: {response.status_code}")
        
        return model_info
            
    async def load(self) -> bool:
        """
        Load the model into Ollama.
        
        Returns:
            True if loading was successful, False otherwise.
        """
        if self.is_loaded():
            app_logger.info(f"Model {self.model_id} is already loaded")
            return True
            
        try:
            if self._async_client:
                # Use Ollama Python client
                app_logger.info(f"Loading model {self.model_id} with Ollama client")
                await self._async_client.pull(model=self.model_id)
            else:
                # Fallback to requests
                import requests
                app_logger.info(f"Loading model {self.model_id} with requests fallback")
                response = requests.post(
                    f"{self.ollama_base_url}/api/pull",
                    json={"name": self.model_id}
                )
                response.raise_for_status()
                
            self._is_loaded = True
            app_logger.info(f"Successfully loaded model {self.model_id}")
            return True
        except Exception as e:
            app_logger.error(f"Error loading model {self.model_id}: {str(e)}")
            return False
    
    async def unload(self) -> None:
        """
        Unload the model from memory.
        
        Note: Ollama doesn't have a direct 'unload' API, so this is more of a cleanup method.
        """
        # Ollama doesn't directly support unloading models from memory
        # Models are garbage collected by Ollama when not in use
        # This method primarily resets the internal state
        self._is_loaded = False
        app_logger.info(f"Marked model {self.model_id} as unloaded")
    
    async def generate(self, 
                       prompt: str, 
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
            A dictionary containing the generated response and metadata.
        """
        if not self.is_loaded():
            success = await self.load()
            if not success:
                return {"response": "Failed to load model", "error": True}
        
        options = options or {}
        
        try:
            # Prepare the request based on whether it's a chat or completion
            is_chat = False
            messages = None
            system = None
            
            # Check if prompt contains a conversation structure
            if prompt.strip().startswith("[") or prompt.strip().startswith("{"):
                try:
                    parsed = json.loads(prompt)
                    if isinstance(parsed, list) and all(isinstance(m, dict) for m in parsed):
                        messages = parsed
                        is_chat = True
                    elif isinstance(parsed, dict) and "messages" in parsed:
                        messages = parsed["messages"]
                        is_chat = True
                        if "system" in parsed:
                            system = parsed["system"]
                except json.JSONDecodeError:
                    # Not valid JSON, treat as regular prompt
                    pass
            
            # Default to treating as a single message if not structured
            if not is_chat:
                messages = [{"role": "user", "content": prompt}]
                is_chat = True
            
            if self._async_client:
                # Use Ollama Python client
                if tools and self.supports_tools:
                    # Format tools for Ollama API
                    options["tools"] = tools
                
                if images and self.supports_vision:
                    # If there are images, ensure the first message contains them
                    if not messages[0].get("images"):
                        messages[0]["images"] = images
                
                # Call Ollama API
                if is_chat:
                    chat_options = {
                        "model": self.model_id,
                        "messages": messages,
                        "options": options
                    }
                    if system:
                        chat_options["system"] = system
                    
                    response = await self._async_client.chat(**chat_options)
                else:
                    # Fallback to completion API for non-chat
                    response = await self._async_client.generate(
                        model=self.model_id,
                        prompt=prompt,
                        options=options
                    )
                
                # Format the response
                result = {
                    "response": response.get("message", {}).get("content", ""),
                    "done": True
                }
                
                # Handle tool calls if present
                if 'tool_calls' in response.get("message", {}):
                    result["tool_calls"] = response["message"]["tool_calls"]
                
                return result
            else:
                # Fallback to requests
                import requests
                
                if is_chat:
                    payload = {
                        "model": self.model_id,
                        "messages": messages,
                        **options
                    }
                    
                    if system:
                        payload["system"] = system
                    
                    if tools and self.supports_tools:
                        payload["tools"] = tools
                    
                    if images and self.supports_vision:
                        # Images in the first message
                        if isinstance(messages[0], dict) and not messages[0].get("images"):
                            messages[0]["images"] = images
                    
                    response = requests.post(
                        f"{self.ollama_base_url}/api/chat",
                        json=payload
                    )
                else:
                    # Completion API
                    payload = {
                        "model": self.model_id,
                        "prompt": prompt,
                        **options
                    }
                    
                    response = requests.post(
                        f"{self.ollama_base_url}/api/generate",
                        json=payload
                    )
                
                response.raise_for_status()
                data = response.json()
                
                result = {
                    "response": data.get("message", {}).get("content", "") 
                              if is_chat else data.get("response", ""),
                    "done": True
                }
                
                # Handle tool calls if present
                if 'tool_calls' in data.get("message", {}):
                    result["tool_calls"] = data["message"]["tool_calls"]
                
                return result
        except Exception as e:
            app_logger.error(f"Error generating response: {str(e)}")
            return {
                "response": f"Error generating response: {str(e)}",
                "error": True
            }
    
    async def generate_stream(self, 
                            prompt: str, 
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
            
        Yields:
            Response chunks as dictionaries.
        """
        if not self.is_loaded():
            success = await self.load()
            if not success:
                yield {"response": "Failed to load model", "error": True, "done": True}
                return
        
        options = options or {}
        
        try:
            # Similar logic to generate() for parsing prompt
            is_chat = False
            messages = None
            system = None
            
            if prompt.strip().startswith("[") or prompt.strip().startswith("{"):
                try:
                    parsed = json.loads(prompt)
                    if isinstance(parsed, list) and all(isinstance(m, dict) for m in parsed):
                        messages = parsed
                        is_chat = True
                    elif isinstance(parsed, dict) and "messages" in parsed:
                        messages = parsed["messages"]
                        is_chat = True
                        if "system" in parsed:
                            system = parsed["system"]
                except json.JSONDecodeError:
                    pass
            
            if not is_chat:
                messages = [{"role": "user", "content": prompt}]
                is_chat = True
            
            if self._async_client:
                # Use Ollama Python client for streaming
                if tools and self.supports_tools:
                    options["tools"] = tools
                
                if images and self.supports_vision:
                    if not messages[0].get("images"):
                        messages[0]["images"] = images
                
                # Set up streaming options
                stream_options = {
                    "model": self.model_id,
                    "stream": True,
                    "options": options
                }
                
                if is_chat:
                    stream_options["messages"] = messages
                    if system:
                        stream_options["system"] = system
                    
                    # Get streaming generator
                    stream = await self._async_client.chat(**stream_options)
                else:
                    # Fallback to completion API
                    stream_options["prompt"] = prompt
                    stream = await self._async_client.generate(**stream_options)
                
                # Yield chunks from the stream
                async for chunk in stream:
                    if not chunk:
                        continue
                    
                    # Format the chunk
                    if is_chat and "message" in chunk:
                        content = chunk["message"].get("content", "")
                        yield {"response": content}
                    elif "response" in chunk:
                        yield {"response": chunk["response"]}
                    elif "content" in chunk:
                        yield {"response": chunk["content"]}
                    
                # Final done message
                yield {"done": True}
            else:
                # Fallback to requests with SSE parsing
                import requests
                import sseclient
                
                if is_chat:
                    payload = {
                        "model": self.model_id,
                        "messages": messages,
                        "stream": True,
                        **options
                    }
                    
                    if system:
                        payload["system"] = system
                    
                    if tools and self.supports_tools:
                        payload["tools"] = tools
                    
                    if images and self.supports_vision and not messages[0].get("images"):
                        messages[0]["images"] = images
                    
                    response = requests.post(
                        f"{self.ollama_base_url}/api/chat",
                        json=payload,
                        stream=True,
                        headers={"Accept": "text/event-stream"}
                    )
                else:
                    # Completion API
                    payload = {
                        "model": self.model_id,
                        "prompt": prompt,
                        "stream": True,
                        **options
                    }
                    
                    response = requests.post(
                        f"{self.ollama_base_url}/api/generate",
                        json=payload,
                        stream=True,
                        headers={"Accept": "text/event-stream"}
                    )
                
                response.raise_for_status()
                client = sseclient.SSEClient(response)
                
                for event in client.events():
                    if not event.data:
                        continue
                    
                    try:
                        data = json.loads(event.data)
                        if is_chat and "message" in data:
                            content = data["message"].get("content", "")
                            yield {"response": content}
                        elif "response" in data:
                            yield {"response": data["response"]}
                        elif "content" in data:
                            yield {"response": data["content"]}
                        
                        # Check for done flag
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        # If not valid JSON, yield as text
                        yield {"response": event.data}
                
                # Final done message
                yield {"done": True}
                
        except Exception as e:
            app_logger.error(f"Error in stream generation: {str(e)}")
            yield {"response": f"Error in stream generation: {str(e)}", "error": True, "done": True}
    
    async def embed(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        
        Args:
            text: The text to embed.
            
        Returns:
            A list of floats representing the embedding vector.
        """
        if not self.is_embedding_model:
            raise NotImplementedError(f"Model '{self.model_id}' does not support embedding generation.")
        
        if not self.is_loaded():
            success = await self.load()
            if not success:
                raise RuntimeError(f"Failed to load model {self.model_id}")
        
        try:
            if self._async_client:
                # Use Ollama Python client
                response = await self._async_client.embeddings(
                    model=self.model_id,
                    prompt=text
                )
                return response.get("embedding", [])
            else:
                # Fallback to requests
                import requests
                response = requests.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={"model": self.model_id, "prompt": text}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
        except Exception as e:
            app_logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def is_loaded(self) -> bool:
        """Check if the model is currently loaded."""
        # First check the internal _is_loaded flag set by the BaseModel
        if self._is_loaded:
            return True
            
        # If not marked as loaded, check with Ollama API
        try:
            import requests
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                is_loaded = any(model.get("name") == self.model_id for model in models)
                
                # Update the internal state if we find it's actually loaded
                if is_loaded:
                    self._is_loaded = True
                    
                return is_loaded
            return False
        except Exception as e:
            app_logger.error(f"Error checking if model is loaded: {str(e)}")
            return False 