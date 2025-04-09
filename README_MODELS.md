# Ollama Desktop Model Implementation

This document describes the new model handling architecture implemented in Ollama Desktop.

## Architecture

The new model architecture is based on an abstract `BaseModel` class that provides a common interface for different language model implementations:

```
BaseModel (abstract)
    │
    └── OllamaModel (concrete implementation)
```

## Key Components

### `api/base_model.py`

This file defines the abstract `BaseModel` class that all model implementations must inherit from. The class provides:

- A common interface for model operations (load, unload, generate, etc.)
- Standard metadata attributes (architecture, parameters, context length, etc.)
- Abstract methods that must be implemented by specific model implementations

### `api/models/ollama_model.py`

This file contains the `OllamaModel` class, which implements the `BaseModel` interface specifically for Ollama models. Features include:

- Automatic extraction of model metadata using the Ollama CLI and API
- Support for both the official Ollama Python client and a direct API fallback
- Intelligent model parameter detection based on model name patterns
- Support for all Ollama API features (chat, generate, stream, embeddings)
- Error handling with proper fallbacks

### `api/models/__init__.py`

This file contains the `ModelRegistry` class, which provides:

- Centralized management of model instances
- Caching to avoid redundant model creation
- Methods to get, load, and unload models
- Automatic defaults for missing parameters

## Usage Examples

### Basic Model Usage

```python
# Get a model from the registry
model = await model_registry.get_model("llama3.2")

# Load the model
success = await model.load()

# Generate text
response = await model.generate("Tell me about quantum computing")
print(response.get("response"))

# Streaming generation
async for chunk in model.generate_stream("Explain AI"):
    print(chunk.get("response"), end="")

# Unload when done
await model.unload()
```

### API Endpoint Integration

The API endpoints in `ollama_mcp_api.py` have been updated to use the new model registry:

- `GET /models` - Returns detailed metadata for all available models
- `GET /models/{model_id}` - Returns detailed metadata for a specific model
- Model management happens automatically through the registry

## Model Parameters

The system automatically detects and populates model parameters:

| Parameter | Description | Example Values |
|-----------|-------------|---------------|
| `architecture` | The model architecture | llama, mistral, gemma, etc. |
| `parameters` | Model size | 3.2B, 7B, 13B, 70B |
| `context_length` | Maximum token context | 4096, 8192, 131072 |
| `quantization` | Quantization format | Q4_K_M, Q5_K_M, F16 |
| `supports_tools` | Tool/function support | true, false |
| `supports_vision` | Image processing support | true, false |
| `is_embedding_model` | Embedding capability | true, false |

## Testing

Model functionality can be tested using:

- `python -m api.test_models` - Tests all available models
- `python test_specific_model.py` - Tests a specific model (llama3.2 by default)

## Future Enhancements

Possible extensions to this architecture include:

- Add support for other model providers (OpenAI, Anthropic, etc.)
- Add GPU/CPU usage monitoring
- Implement more sophisticated model loading/unloading strategies
- Add better parameter detection for more model types 