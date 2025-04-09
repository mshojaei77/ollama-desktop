"""
Test script for a specific model

This script demonstrates how to use the BaseModel implementation
with a specific Ollama model.
"""

import asyncio
import json
import sys
import os

# Add the necessary paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Try direct imports
    from api.models.ollama_model import OllamaModel
except ImportError:
    # Fall back to adjusting path and reimporting
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "api"))
    from models.ollama_model import OllamaModel

async def test_specific_model():
    """Test a specific model"""
    # Test with llama3.2
    model_id = "llama3.2"
    
    # Create model instance
    try:
        print(f"\nTesting model: {model_id}")
        model = OllamaModel(model_id=model_id)
        
        # Print model metadata
        metadata = model.get_metadata()
        print("Model Metadata:")
        print(json.dumps(metadata, indent=2))
        
        # Load model
        print("\nLoading model...")
        loaded = await model.load()
        print(f"Model loaded: {loaded}")
        
        # Generate text with specific parameters
        prompt = "Explain Ollama desktop in one paragraph:"
        print(f"\nPrompt: {prompt}")
        
        response = await model.generate(prompt, {
            "temperature": 0.7,
            "top_p": 0.9
        })
        print("\nResponse:")
        print(response.get("response", "No response"))
        
        # Test unloading
        print("\nUnloading model...")
        await model.unload()
        print("Model unloaded")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

# Run the test
if __name__ == "__main__":
    asyncio.run(test_specific_model()) 