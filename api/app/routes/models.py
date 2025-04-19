from fastapi import APIRouter, HTTPException
from app.core.chatbot import OllamaMCPPackage, app_logger
import time
import json
import asyncio
from fastapi.responses import StreamingResponse
from api.app.database.database import db
from app.core.config import get_cache_expiry_seconds

router = APIRouter(prefix="/models", tags=["Models"])

# Import scraper functions
from app.services.scrape_ollama import (
    fetch_popular_models,
    fetch_vision_models,
    fetch_tools_models,
    fetch_newest_models,
    fetch_embedding_models
)

@router.get("/available-models", tags=["Models"])
async def get_available_models():
    """
    Get list of available Ollama models
    
    - Returns all models currently available in the Ollama environment
    - Does not require an active session
    """
    try:
        models = await OllamaMCPPackage.get_available_models()
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")


@router.get("/recent")
async def get_recent_models(limit: int = 5):
    """Get recently used models"""
    try:
        models = await db.get_recently_used_models(limit)
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting recent models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recent models: {str(e)}")

@router.get("/", tags=["Models"])
async def get_models():
    """
    Get all available models from Ollama.

    Models are fetched directly from Ollama and cached in memory for 5 minutes.
    """
    global _model_cache
    current_time = time.time()

    # Check cache
    if _model_cache and (current_time - _model_cache.get('timestamp', 0)) < get_cache_expiry_seconds():
        app_logger.info("Returning cached models.")
        return {"models": _model_cache['models']}

    try:
        app_logger.info("Fetching models directly from Ollama.")
        # 1. Get currently available models from Ollama
        # This function should ideally return List[Dict[str, Any]] or List[str]
        available_models = await OllamaMCPPackage.get_available_models()
        app_logger.info(f"Available models fetched from Ollama: {available_models}")

        # 2. Format the models for the response (handle list of strings or dicts)
        models_list = []
        if available_models:
             for model_info in available_models:
                if isinstance(model_info, dict):
                    # Ensure 'name' key exists, include other fields if present
                    model_data = {
                        'name': model_info.get('name', 'Unknown Model Name'),
                        **{k: v for k, v in model_info.items() if k != 'name'}
                    }
                    models_list.append(model_data)
                elif isinstance(model_info, str):
                    # If it's just a string, create a basic dictionary
                    models_list.append({"name": model_info})
                else:
                     app_logger.warning(f"Unexpected model info format received from Ollama: {model_info}")
        else:
             app_logger.warning("Received empty or null model list from Ollama.")


        # 3. Update cache
        _model_cache = {
            'models': models_list,
            'timestamp': current_time
        }
        app_logger.info(f"Updated model cache with {len(models_list)} models.")

        return {"models": models_list}

    except Exception as e:
        app_logger.error(f"Error getting models directly from Ollama: {str(e)}", exc_info=True)
        # If fetching fails, raise error. Consider returning stale cache if critical.
        raise HTTPException(status_code=500, detail=f"Error getting models from Ollama: {str(e)}")

@router.get("/{model_name:path}/info", tags=["Models"])
async def get_specific_model_info(model_name: str):
    """
    Get curated information about a specific Ollama model.

    Uses the cleaned-up function to return specific fields like family,
    parameter size, quantization level, languages, etc.

    Args:
        model_name: The name of the model (e.g., 'llama3.2')

    Returns:
        A dictionary containing the curated model information.
        Returns 404 if the model is not found.
    """
    try:
        app_logger.info(f"Getting curated info for model: {model_name}")
        model_info = await OllamaMCPPackage.get_model_info(model_name)

        if not model_info:
            # The underlying function returns {} if model not found or on error
            app_logger.warning(f"Model info not found for: {model_name}")
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found or error retrieving info.")

        return model_info

    except HTTPException as http_exc:
        # Re-raise HTTPExceptions (like 404) directly
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error getting specific model info for '{model_name}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error retrieving info for model '{model_name}'")


# Add scraped models endpoint
@router.get("/scraped", tags=["Models"])
async def get_scraped_models():
    """
    Scrape models from ollama.com and return popular, vision, tools, and newest models.
    """
    try:
        popular = await asyncio.to_thread(fetch_popular_models)
        vision = await asyncio.to_thread(fetch_vision_models)
        tools = await asyncio.to_thread(fetch_tools_models)
        newest = await asyncio.to_thread(fetch_newest_models)
        embedding = await asyncio.to_thread(fetch_embedding_models)
        return {
            "popular": popular,
            "vision": vision,
            "tools": tools,
            "newest": newest,
            "embedding": embedding
        }
    except Exception as e:
        app_logger.error(f"Error scraping models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scraping models: {str(e)}")

# Add endpoint for pulling models with progress streaming
@router.get("/{model_name}/pull", tags=["Models"])
async def pull_model_endpoint(model_name: str, stream: bool = True):
    """
    Pull the specified Ollama model and stream progress updates as newline-delimited JSON.
    """
    def iter_progress():
        for progress in OllamaMCPPackage.pull_model(model_name, stream=stream):
            # Convert to plain dict for JSON serialization
            if isinstance(progress, dict):
                progress_data = progress
            elif hasattr(progress, "dict") and callable(progress.dict):
                progress_data = progress.dict()
            else:
                try:
                    progress_data = vars(progress)
                except Exception:
                    progress_data = progress
            # Fallback to default=str for any non-serializable values
            yield json.dumps(progress_data, default=str) + "\n"
    return StreamingResponse(iter_progress(), media_type="application/x-ndjson")
