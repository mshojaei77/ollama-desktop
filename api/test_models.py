"""
Test script for the BaseModel implementation

This script demonstrates how to use the BaseModel implementation
for Ollama models.
"""

import asyncio
import json
import os
import sys

# Add the parent directory to the module search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import model_registry
from logger import app_logger

async def test_model_registry():
    """Test the model registry functionality"""
    try:
        # Get all available models
        print("\n=== All Available Models ===")
        models = await model_registry.get_all_models()
        
        for i, model in enumerate(models, 1):
            model_id = model.get("id")
            name = model.get("name")
            params = model.get("parameters")
            arch = model.get("architecture")
            quant = model.get("quantization")
            
            print(f"{i}. {name} ({model_id})")
            print(f"   Architecture: {arch}, Parameters: {params}, Quantization: {quant}")
        
        # No models available
        if not models:
            print("No models available. Please make sure Ollama is running.")
            return
        
        # Select a model to test
        model_to_test = models[0]["id"]  # Use the first model by default
        
        # Try to find llama3.2 if available
        for model in models:
            if model["id"] == "llama3.2":
                model_to_test = "llama3.2"
                break
                
        print(f"\n=== Testing Model: {model_to_test} ===")
        
        # Get the model
        model = await model_registry.get_model(model_to_test)
        if not model:
            print(f"Could not get model {model_to_test}")
            return
        
        # Print model metadata
        metadata = model.get_metadata()
        print("Model Metadata:")
        print(json.dumps(metadata, indent=2))
        
        # Test loading the model
        print("\nLoading model...")
        loaded = await model.load()
        print(f"Model loaded: {loaded}")
        
        # Test generating text
        print("\nGenerating text...")
        response = await model.generate("What is artificial intelligence?")
        print("\nResponse:")
        print(response.get("response", "No response"))
        
        # Test streaming text
        print("\nStreaming text...")
        prompt = "Explain quantum computing in one paragraph."
        print(f"Prompt: {prompt}")
        print("\nResponse:")
        
        # Stream the response
        full_response = []
        async for chunk in model.generate_stream(prompt):
            if "response" in chunk:
                print(chunk["response"], end="", flush=True)
                full_response.append(chunk["response"])
            if chunk.get("done", False):
                break
        
        print("\n\nDone streaming.")
        
        # Test unloading the model
        print("\nUnloading model...")
        await model.unload()
        print("Model unloaded")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Clean up
        await model_registry.cleanup()
        print("\nModel registry cleaned up")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_model_registry()) 