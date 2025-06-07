"""
Ollama API - Integration example with FastAPI
run with: uvicorn ollama_api_server:app --reload
or python -m uvicorn ollama_api_server:app --reload
"""

import os
import json
import asyncio
import webbrowser  # Add this import
import threading
import time
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
import tempfile
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

# Add sys import and path modification
import sys
import os
# Ensure the parent directory (containing the 'api' package) is in the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from api.ollama_client import OllamaPackage, OllamaMCPAgent, app_logger
from api import db  # Import our new database module
from api.config_io import read_ollama_config, write_ollama_config
from api.mcp_agents.routes import router as mcp_agents_router  # Import the MCP agents router

# Import system prompt management functions
from api.config_io import (
    get_active_system_prompt, 
    set_active_system_prompt, 
    save_system_prompt, 
    delete_system_prompt, 
    get_all_system_prompts
)

# Import scraper functions
from api.scrape_ollama import (
    fetch_popular_models,
    fetch_vision_models,
    fetch_tools_models,
    fetch_newest_models,
    fetch_embedding_models
)

# Add these imports at the top with other imports
import signal
import psutil
import subprocess

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app startup and shutdown events"""
    # Startup
    db.init_db()
    db.migrate_database()
    app_logger.info("Database initialized and migrated")
    
    app_logger.info("MCP agents will be initialized via the MCP agents router")
    
    # Start Ollama on Windows platforms
    if sys.platform.startswith('win'):
        try:
            subprocess.Popen(['powershell', '-Command', 'ollama list'], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            app_logger.error(f"Failed to start Ollama: {str(e)}")
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down application, cleaning up resources...")
    app_logger.info("MCP agents cleanup will be handled by the MCP agents router")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Ollama Desktop API",
    description="API for interacting with Ollama models",
    version="1.0.0",
    docs_url="/docs",              # Explicitly set Swagger UI endpoint (default)
    redoc_url="/redoc",            # Also enable ReDoc (alternative docs)
    openapi_url="/openapi.json",   # URL for the OpenAPI schema
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Chat",
            "description": "Operations for working with standalone Ollama agents"
        },
        {
            "name": "Sessions",
            "description": "Operations for managing sessions and retrieving chat history"
        },
        {
            "name": "Models",
            "description": "Operations for getting information about available models"
        },
        {
            "name": "MCP Agents",
            "description": "Operations for working with MCP (Model Context Protocol) agents"
        },
        {
            "name": "Context",
            "description": "Operations for adding context from files to sessions"
        },
        {
            "name": "System Prompts",
            "description": "Operations for managing user-configurable system prompts"
        }
    ]
)

# Add this right after creating the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the MCP agents router
app.include_router(mcp_agents_router)

# Global state for agents
active_agents: Dict[str, OllamaMCPAgent] = {}

# Global cache for models
_model_cache: Optional[Dict[str, Any]] = None
_CACHE_EXPIRY_SECONDS = 300 # Cache models for 5 minutes

# ----- Pydantic Models for Request/Response -----

class ChatRequest(BaseModel):
    message: str
    session_id: str
    
class ChatResponse(BaseModel):
    response: str
    session_id: str

class InitializeRequest(BaseModel):
    model_name: str = "llama3.2"
    system_message: Optional[str] = None
    session_id: Optional[str] = None
    
class InitializeResponse(BaseModel):
    session_id: str
    status: str
    model: str

class StatusResponse(BaseModel):
    status: str
    active_sessions: List[str]
    message: Optional[str] = None

class ChatHistoryItem(BaseModel):
    role: str
    message: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[ChatHistoryItem]
    count: int

class ChatSession(BaseModel):
    session_id: str
    model_name: str
    session_type: str
    system_message: Optional[str] = None
    created_at: str
    last_active: str
    is_active: bool
    message_count: Optional[int] = 0
    first_message_time: Optional[str] = None
    last_message_time: Optional[str] = None

class AvailableChatsResponse(BaseModel):
    sessions: List[ChatSession]
    count: int

# System Prompt Models
class SystemPromptConfig(BaseModel):
    name: str
    description: str
    instructions: List[str]
    additional_context: Optional[str] = ""
    expected_output: Optional[str] = ""
    markdown: bool = True
    add_datetime_to_instructions: bool = False

class SystemPrompt(BaseModel):
    id: str
    config: SystemPromptConfig

class SystemPromptsResponse(BaseModel):
    prompts: List[SystemPrompt]
    active_prompt_id: str

class SetActivePromptRequest(BaseModel):
    prompt_id: str

class SavePromptRequest(BaseModel):
    prompt_id: str
    config: SystemPromptConfig

# ----- Helper Functions -----

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return f"session-{uuid.uuid4()}"

async def cleanup_session(session_id: str):
    """Clean up resources for a session"""
    # 1. Clean up in-memory resources (agents)
    if session_id in active_agents:
        await active_agents[session_id].cleanup()
        del active_agents[session_id]
        app_logger.info(f"Cleaned up agent session: {session_id}")
    
    # 2. Permanently delete session and history from the database
    try:
        await db.delete_session_permanently(session_id)
    except Exception as e:
        app_logger.error(f"Error permanently deleting session {session_id} from database: {str(e)}")

ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf"}


# ----- API Endpoints -----

@app.get("/", tags=["Status"])
async def root():
    """Root endpoint providing API status information"""
    return {
        "status": "ok",
        "service": "Ollama Desktop API",
        "active_sessions": len(active_agents)
    }

@app.post("/chat/initialize", response_model=InitializeResponse, tags=["Chat"])
async def initialize_agent(request: InitializeRequest):
    """
    Initialize a standalone Ollama agent
    
    - Creates a new agent with the specified model
    - Returns a session ID for subsequent interactions
    - Optionally accepts a system message to customize the agent's behavior
    """
    try:
        # Validate model name is not empty
        if not request.model_name or request.model_name.strip() == "":
            raise HTTPException(status_code=400, detail="Model name cannot be empty")
        
        session_id = request.session_id or generate_session_id()
        
        # Clean up existing session if it exists
        if session_id in active_agents:
            await cleanup_session(session_id)
        
        # Log the initialization attempt with the model name
        app_logger.info(f"Initializing agent with model: {request.model_name}")
        
        # Create new agent using the new API with system prompt configuration
        # For backward compatibility, create a basic agent without MCP by default
        agent = await OllamaPackage.create_agent(
            model_name=request.model_name,
            system_message=request.system_message,
            session_id=session_id,
            verbose=True,
            use_config_system_prompt=True,  # Use configured system prompts by default
        )
        
        # Custom tools are already added during agent creation
        
        # Store in active sessions
        active_agents[session_id] = agent
        
        # Save to database
        await db.create_session(
            session_id=session_id,
            model_name=request.model_name,
            session_type="agent",
            system_message=request.system_message
        )
        
        return InitializeResponse(
            session_id=session_id,
            status="ready",
            model=request.model_name
        )
    except ValueError as e:
        # Handle specific value errors
        app_logger.error(f"Value error initializing agent: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly so FastAPI handles them correctly
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error initializing agent: {str(e)}", exc_info=True)
        # Handle other unexpected errors as 500
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/message", response_model=ChatResponse, tags=["Chat"])
async def chat_message(request: ChatRequest):
    """
    Send a message to an agent
    
    - Requires a valid session_id from a previous /chat/initialize call
    - Returns the model's response to the user message
    - Saves the conversation history to the database
    """
    if request.session_id not in active_agents:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        agent = active_agents[request.session_id]
        
        # Save user message to history
        await db.add_chat_message(request.session_id, "user", request.message)
        
        # Get response from agent
        response = await agent.chat(request.message)
        
        # Save assistant response to history
        await db.add_chat_message(request.session_id, "assistant", response)
        
        # Update session activity
        await db.update_session_activity(request.session_id)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@app.post("/chat/message/stream", tags=["Chat"])
async def chat_message_stream(request: ChatRequest):
    """
    Send a message to an agent and stream the response using SSE
    
    - Requires a valid session_id from a previous /chat/initialize call
    - Returns a streaming response from the model
    - Saves the conversation history to the database once completed
    """
    if request.session_id not in active_agents:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response from Ollama"""
        try:
            agent = active_agents[request.session_id]
            
            # Save user message to history
            await db.add_chat_message(request.session_id, "user", request.message)
            
            # Log the request to help with debugging
            app_logger.info(f"Starting stream for message: {request.message[:50]}...")
            
            try:
                # Try Agno's native streaming capabilities first
                full_response = []
                streamed_successfully = False
                
                try:
                    # Get streaming response from Agno agent
                    run_response = agent.agent.run(request.message, stream=True)
                    
                    for chunk in run_response:
                        if hasattr(chunk, 'content') and chunk.content:
                            # Stream content in small chunks to preserve formatting but reduce overhead
                            content = chunk.content
                            full_response.append(content)
                            
                            # Split content into words but preserve spaces and newlines
                            import re
                            parts = re.findall(r'\S+|\s+', content)
                            for part in parts:
                                yield f"data: {json.dumps({'text': part})}\n\n"
                                await asyncio.sleep(0.02)  # Small delay for streaming effect
                            
                            streamed_successfully = True
                            
                except Exception as stream_error:
                    app_logger.warning(f"Agno streaming failed: {stream_error}, falling back to regular chat")
                
                # If Agno streaming didn't work, fall back to regular chat
                if not streamed_successfully:
                    app_logger.info("Using fallback streaming method")
                    response = await agent.chat(request.message)
                    full_response = [response]
                    
                    # Stream word by word while preserving all whitespace characters
                    import re
                    parts = re.findall(r'\S+|\s+', response)
                    for part in parts:
                        # Send all parts including spaces and newlines
                        yield f"data: {json.dumps({'text': part})}\n\n"
                        await asyncio.sleep(0.03)  # Slightly longer delay for fallback
                
                complete_response = ''.join(full_response)
                
                # Update session activity
                await db.update_session_activity(request.session_id)
                
                # Save assistant response to history
                await db.add_chat_message(request.session_id, "assistant", complete_response)
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                app_logger.error(f"Error during streaming: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                raise
            
        except Exception as e:
            app_logger.error(f"Error streaming chat message: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )

@app.get("/available-models", tags=["Models"])
async def get_available_models():
    """
    Get list of available Ollama models
    
    - Returns all models currently available in the Ollama environment
    - Does not require an active session
    """
    try:
        models = await OllamaPackage.get_available_models()
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")

@app.get("/models", tags=["Models"])
async def get_models():
    """
    Get all available models from Ollama.

    Models are fetched directly from Ollama and cached in memory for 5 minutes.
    """
    global _model_cache
    current_time = time.time()

    # Check cache
    if _model_cache and (current_time - _model_cache.get('timestamp', 0)) < _CACHE_EXPIRY_SECONDS:
        app_logger.info("Returning cached models.")
        return {"models": _model_cache['models']}

    try:
        app_logger.info("Fetching models directly from Ollama.")
        # 1. Get currently available models from Ollama
        # This function should ideally return List[Dict[str, Any]] or List[str]
        available_models = await OllamaPackage.get_available_models()
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

@app.get("/models/{model_name:path}/info", tags=["Models"])
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
        model_info = await OllamaPackage.get_model_info(model_name)

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

@app.get("/chats", response_model=AvailableChatsResponse, tags=["Sessions"])
async def get_chats(
    include_inactive: bool = False,
    limit: int = 100,
    offset: int = 0
):
    try:
        db_sessions = await db.get_sessions_with_message_count(
            include_inactive=include_inactive,
            limit=limit,
            offset=offset
        )
        
        sessions = []
        for session in db_sessions:
            # Convert timestamp fields to strings if they're datetime objects
            created_at = session["created_at"]
            last_active = session["last_active"]
            first_message_time = session.get("first_message_time")
            last_message_time = session.get("last_message_time")
            message_count = session.get("message_count", 0)

            if message_count < 1:
                continue

            sessions.append(ChatSession(
                session_id=session["session_id"],
                model_name=session["model_name"],
                session_type=session["session_type"],
                system_message=session["system_message"],
                created_at=created_at,
                last_active=last_active,
                is_active=session["is_active"],
                message_count=message_count,
                first_message_time=first_message_time,
                last_message_time=last_message_time
            ))
        
        return AvailableChatsResponse(
            sessions=sessions,
            count=len(sessions)
        )
    except Exception as e:
        app_logger.error(f"Error getting chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting chats: {str(e)}")

@app.get("/chats/search", response_model=AvailableChatsResponse, tags=["Sessions"])
async def search_chats(
    q: str,
    include_inactive: bool = False,
    limit: int = 100,
    offset: int = 0
):
    """
    Search for chat sessions by keyword
    
    - Searches in message content, model names, and system messages
    - Returns matching chat sessions with message counts and metadata
    - Can include inactive sessions with the include_inactive parameter
    - Supports pagination with limit and offset parameters
    
    Args:
        q: Search query string
        include_inactive: Whether to include inactive sessions (default: False)
        limit: Maximum number of sessions to return (default: 100)
        offset: Number of sessions to skip for pagination (default: 0)
    """
    try:
        # Search for sessions in the database
        db_sessions = await db.search_chats(
            search_term=q,
            include_inactive=include_inactive,
            limit=limit,
            offset=offset
        )
        
        # Convert to response model
        sessions = []
        for session in db_sessions:
            # Convert timestamp fields to strings if they're datetime objects
            created_at = session["created_at"]
            last_active = session["last_active"]
            first_message_time = session.get("first_message_time")
            last_message_time = session.get("last_message_time")
            
            sessions.append(ChatSession(
                session_id=session["session_id"],
                model_name=session["model_name"],
                session_type=session["session_type"],
                system_message=session["system_message"],
                created_at=created_at,
                last_active=last_active,
                is_active=session["is_active"],
                message_count=session.get("message_count", 0),
                first_message_time=first_message_time,
                last_message_time=last_message_time
            ))
        
        return AvailableChatsResponse(
            sessions=sessions,
            count=len(sessions)
        )
    except Exception as e:
        app_logger.error(f"Error searching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching chats: {str(e)}")

@app.get("/models/recent")
async def get_recent_models(limit: int = 5):
    """Get recently used models"""
    try:
        models = await db.get_recently_used_models(limit)
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting recent models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recent models: {str(e)}")

@app.post("/sessions/{session_id}/upload_file", tags=["Context"])
async def upload_file_to_session(session_id: str, file: UploadFile = File(...)):
    """
    Upload a file (.txt, .md, .pdf) to add its content as context to a session.

    - Validates the session ID and file type.
    - Saves the file temporarily.
    - Processes the file content and adds it to the session's context.
    - Cleans up the temporary file.
    """
    agent: Optional[OllamaAgent] = None

    # Check if session exists in active_agents
    if session_id in active_agents:
        agent = active_agents[session_id]
    else:
        # Verify if the session exists in the database but isn't active in memory
        db_session = await db.get_session(session_id)
        if db_session:
             # Session exists but isn't loaded. We could potentially load it here,
             # but for simplicity, let's require it to be active.
             # Or, we could decide to initialize it on the fly if needed.
             raise HTTPException(status_code=404, detail=f"Session {session_id} exists but is not currently active. Please initialize it first.")
        else:
             raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    if not agent:
         raise HTTPException(status_code=500, detail=f"Could not retrieve agent instance for session {session_id}.")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions are: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Create a temporary directory to store the uploaded file
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = Path(temp_dir) / file.filename

        # Save the uploaded file to the temporary path
        try:
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            app_logger.info(f"Temporarily saved uploaded file to: {temp_file_path}")
        except Exception as e:
             app_logger.error(f"Failed to save uploaded file: {e}")
             raise HTTPException(status_code=500, detail="Failed to save uploaded file.")
        finally:
             # Ensure the file pointer is closed, even if copyfileobj fails
             file.file.close()

        # Process the file using the agent's method
        try:
            await agent.add_file_context(temp_file_path, file.filename)
            app_logger.info(f"Successfully processed file context for session {session_id} from {file.filename}")
            return {"message": f"File '{file.filename}' processed and added to context for session {session_id}"}
        except FileNotFoundError as e:
             app_logger.error(f"File not found during processing: {e}")
             raise HTTPException(status_code=500, detail="Internal error: Saved file could not be found for processing.")
        except ImportError as e:
            # Specifically catch missing pypdf
            if "pypdf" in str(e):
                app_logger.error(f"PDF processing error for {file.filename}: {e}")
                raise HTTPException(status_code=400, detail="Cannot process PDF file: pypdf library is not installed.")
            else:
                app_logger.error(f"Import error during processing {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Internal server error during file processing: {e}")
        except Exception as e:
            app_logger.error(f"Failed to process file context for session {session_id}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    # The temporary directory and its contents (temp_file_path) are automatically removed here
    # when the 'with' block exits.

# Add Vision Chat endpoint
@app.post("/chat/vision", response_model=ChatResponse, tags=["Chat"])
async def chat_vision(
    session_id: str = Form(...),
    message: str = Form(...),
    images: List[UploadFile] = File(...)
):
    """
    Chat with image(s) using the vision model.
    - Requires a valid session_id from a previous /chat/initialize call
    - Accepts multiple images.
    """
    # Retrieve agent instance
    if session_id in active_agents:
        agent = active_agents[session_id]
    else:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    # Save user message and update activity
    await db.add_chat_message(session_id, "user", message + f" [images: {[file.filename for file in images]}]")
    await db.update_session_activity(session_id)
    # Save uploaded images to a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_image_paths = []
        for file in images:
            temp_path = Path(temp_dir) / file.filename
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            temp_image_paths.append(str(temp_path))
        # Call the vision chat method
        response_content = await agent.chat_with_image(message, temp_image_paths)
    # Save assistant response
    await db.add_chat_message(session_id, "assistant", response_content)
    await db.update_session_activity(session_id)
    return ChatResponse(response=response_content, session_id=session_id)

# Add scraped models endpoint
@app.get("/models/scraped", tags=["Models"])
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
@app.get("/models/{model_name}/pull", tags=["Models"])
async def pull_model_endpoint(model_name: str, stream: bool = True):
    """
    Pull the specified Ollama model and stream progress updates as newline-delimited JSON.
    """
    def iter_progress():
        for progress in OllamaPackage.pull_model(model_name, stream=stream):
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

# ----- System Prompt Endpoints -----

@app.get("/system-prompts", response_model=SystemPromptsResponse, tags=["System Prompts"])
async def get_system_prompts():
    """
    Get all available system prompts and the currently active one.
    
    Returns a list of all configured system prompts along with the ID of the active prompt.
    """
    try:
        # Get all system prompts
        all_prompts = get_all_system_prompts()
        
        # Get active prompt ID
        config = read_ollama_config()
        active_prompt_id = config.get("activeSystemPrompt", "default") if config else "default"
        
        # Convert to response format
        prompts = []
        for prompt_id, prompt_config in all_prompts.items():
            prompts.append(SystemPrompt(
                id=prompt_id,
                config=SystemPromptConfig(**prompt_config)
            ))
        
        return SystemPromptsResponse(
            prompts=prompts,
            active_prompt_id=active_prompt_id
        )
    except Exception as e:
        app_logger.error(f"Error getting system prompts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system prompts: {str(e)}")

@app.get("/system-prompts/active", response_model=SystemPrompt, tags=["System Prompts"])
async def get_active_system_prompt_endpoint():
    """
    Get the currently active system prompt configuration.
    
    Returns the configuration of the system prompt that is currently active.
    """
    try:
        # Get active prompt config
        active_config = get_active_system_prompt()
        if not active_config:
            raise HTTPException(status_code=404, detail="No active system prompt found")
        
        # Get the active prompt ID
        config = read_ollama_config()
        active_prompt_id = config.get("activeSystemPrompt", "default") if config else "default"
        
        return SystemPrompt(
            id=active_prompt_id,
            config=SystemPromptConfig(**active_config)
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting active system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting active system prompt: {str(e)}")

@app.post("/system-prompts/active", tags=["System Prompts"])
async def set_active_system_prompt_endpoint(request: SetActivePromptRequest):
    """
    Set the active system prompt.
    
    Changes which system prompt is currently active for new agent sessions.
    Existing sessions will continue using their original prompt until reinitialized.
    """
    try:
        success = set_active_system_prompt(request.prompt_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to set active system prompt to '{request.prompt_id}'")
        
        app_logger.info(f"Set active system prompt to: {request.prompt_id}")
        return {"status": "success", "message": f"Active system prompt set to '{request.prompt_id}'"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error setting active system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error setting active system prompt: {str(e)}")

@app.post("/system-prompts", tags=["System Prompts"])
async def save_system_prompt_endpoint(request: SavePromptRequest):
    """
    Save a system prompt configuration.
    
    Creates a new system prompt or updates an existing one with the provided configuration.
    The prompt can then be activated and used for new agent sessions.
    """
    try:
        # Convert Pydantic model to dict
        prompt_config = request.config.model_dump()
        
        success = save_system_prompt(request.prompt_id, prompt_config)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to save system prompt '{request.prompt_id}'")
        
        app_logger.info(f"Saved system prompt: {request.prompt_id}")
        return {"status": "success", "message": f"System prompt '{request.prompt_id}' saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error saving system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving system prompt: {str(e)}")

@app.get("/system-prompts/{prompt_id}", response_model=SystemPrompt, tags=["System Prompts"])
async def get_system_prompt_by_id(prompt_id: str):
    """
    Get a specific system prompt by ID.
    
    Returns the configuration of the specified system prompt.
    """
    try:
        all_prompts = get_all_system_prompts()
        if prompt_id not in all_prompts:
            raise HTTPException(status_code=404, detail=f"System prompt '{prompt_id}' not found")
        
        prompt_config = all_prompts[prompt_id]
        return SystemPrompt(
            id=prompt_id,
            config=SystemPromptConfig(**prompt_config)
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting system prompt '{prompt_id}': {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting system prompt: {str(e)}")

@app.delete("/system-prompts/{prompt_id}", tags=["System Prompts"])
async def delete_system_prompt_endpoint(prompt_id: str):
    """
    Delete a system prompt configuration.
    
    Removes the specified system prompt. Cannot delete the 'default' prompt.
    If the deleted prompt was active, the system will switch back to 'default'.
    """
    try:
        if prompt_id == "default":
            raise HTTPException(status_code=400, detail="Cannot delete the default system prompt")
        
        success = delete_system_prompt(prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"System prompt '{prompt_id}' not found or could not be deleted")
        
        app_logger.info(f"Deleted system prompt: {prompt_id}")
        return {"status": "success", "message": f"System prompt '{prompt_id}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error deleting system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting system prompt: {str(e)}")

@app.post("/sessions/{session_id}/update-prompt", tags=["System Prompts"])
async def update_session_system_prompt(session_id: str, request: SetActivePromptRequest):
    """
    Update the system prompt for an active session.
    
    Changes the system prompt for an existing session. The session must be active in memory.
    This allows users to change the behavior of an ongoing conversation.
    """
    try:
        if session_id not in active_agents:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or not active")
        
        # Get the prompt configuration
        all_prompts = get_all_system_prompts()
        if request.prompt_id not in all_prompts:
            raise HTTPException(status_code=404, detail=f"System prompt '{request.prompt_id}' not found")
        
        prompt_config = all_prompts[request.prompt_id]
        
        # Update the agent's system prompt
        agent = active_agents[session_id]
        agent.update_system_prompt(prompt_config)
        
        app_logger.info(f"Updated system prompt for session {session_id} to: {request.prompt_id}")
        return {"status": "success", "message": f"Session {session_id} updated to use system prompt '{request.prompt_id}'"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error updating session system prompt: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating session system prompt: {str(e)}")

@app.post("/cleanup")
async def cleanup_endpoint():
    """Endpoint to handle cleanup requests from the frontend"""
    try:
        app_logger.info("Received cleanup request")
        
        # Schedule the shutdown after response is sent
        async def shutdown():
            await asyncio.sleep(1)  # Give time for response to be sent
            cleanup_processes()
            
        asyncio.create_task(shutdown())
        return {"status": "success", "message": "Cleanup scheduled"}
    except Exception as e:
        app_logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during cleanup: {str(e)}")

# Add this function before the start_server function
def cleanup_processes():
    """Clean up all running processes"""
    try:
        # Get the current process
        current_process = psutil.Process()
        
        # Get all child processes
        children = current_process.children(recursive=True)
        
        # Terminate frontend process if running
        for child in children:
            try:
                # Check if process is npm/node (frontend)
                if child.name().lower() in ['npm', 'node', 'npm.cmd', 'node.exe']:
                    child.terminate()
                    app_logger.info(f"Terminated process: {child.name()}")
            except Exception as e:
                app_logger.error(f"Error terminating process {child.name()}: {str(e)}")
        
        # Allow time for graceful termination
        psutil.wait_procs(children, timeout=3)
        
        # Force kill any remaining processes
        for child in children:
            try:
                if child.is_running():
                    child.kill()
            except Exception as e:
                app_logger.error(f"Error killing process: {str(e)}")
        
        app_logger.info("All child processes cleaned up")

        # Exit the current process (which will close the terminal)
        if not getattr(sys, 'frozen', False):  # If running from source (not packaged)
            current_process.terminate()
        
    except Exception as e:
        app_logger.error(f"Error in cleanup_processes: {str(e)}")

# Add signal handlers
def signal_handler(signum, frame):
    """Handle termination signals"""
    app_logger.info(f"Received signal {signum}")
    cleanup_processes()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
if sys.platform.startswith('win'):
    signal.signal(signal.SIGBREAK, signal_handler)

def start_server():
    """Start the FastAPI server"""
    # Ensure Ollama is running
    if not ensure_ollama_running():
        app_logger.error("Failed to ensure Ollama is running. Please start Ollama manually.")
        sys.exit(1)
        
    # Start frontend in a separate terminal
    start_frontend()
    
    try:
        # Start the API server
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        app_logger.info("Received keyboard interrupt")
        cleanup_processes()
    except Exception as e:
        app_logger.error(f"Error running server: {str(e)}")
        cleanup_processes()
        raise

def start_frontend():
    """Start the Electron app"""
    try:
        # Get the absolute path to the front directory
        front_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'front'))
        
        # First ensure all dependencies are installed
        if sys.platform.startswith('win'):
            npm_cmd = 'npm.cmd'
        else:
            npm_cmd = 'npm'
            
        # Run npm install first
        try:
            subprocess.run(
                [npm_cmd, 'install'],
                cwd=front_dir,
                check=True,
                capture_output=True
            )
            app_logger.info("Frontend dependencies installed")
        except subprocess.CalledProcessError as e:
            app_logger.error(f"Failed to install frontend dependencies: {e.stderr.decode()}")
            raise
            
        # Set environment variables
        env = dict(os.environ)
        env['NODE_ENV'] = 'production'  # Force production mode
        
        # Start the Electron app
        if sys.platform.startswith('win'):
            electron_process = subprocess.Popen(
                [npm_cmd, 'run', 'start'],
                cwd=front_dir,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            electron_process = subprocess.Popen(
                [npm_cmd, 'run', 'start'],
                cwd=front_dir,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        app_logger.info("Started Electron app")
        
    except Exception as e:
        app_logger.error(f"Failed to start frontend: {str(e)}")
        raise

def ensure_ollama_running():
    """Check if Ollama is running and start it if not"""
    import subprocess
    import time
    import requests
    
    def is_ollama_running():
        try:
            response = requests.get("http://localhost:11434/api/version")
            return response.status_code == 200
        except requests.exceptions.ConnectionError:
            return False
    
    # First check if Ollama is already running
    if is_ollama_running():
        app_logger.info("Ollama is already running")
        return True
        
    # If not running, try to start it
    try:
        if sys.platform.startswith('win'):
            # Windows
            subprocess.Popen(['powershell', '-Command', 'ollama serve'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Linux/MacOS
            subprocess.Popen(['ollama', 'serve'])
            
        # Wait for Ollama to start (max 30 seconds)
        for _ in range(30):
            if is_ollama_running():
                app_logger.info("Successfully started Ollama")
                return True
            time.sleep(1)
            
        app_logger.error("Timeout waiting for Ollama to start")
        return False
        
    except Exception as e:
        app_logger.error(f"Failed to start Ollama: {str(e)}")
        return False

@app.delete("/sessions/{session_id}", response_model=StatusResponse)
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """Delete a session"""
    session_in_memory = session_id in active_agents
    
    # Check if session exists in memory or database
    if not session_in_memory:
        db_session = await db.get_session(session_id)
        if not db_session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
        # Session exists in DB but not memory, still proceed with cleanup/deactivation
        app_logger.info(f"Session {session_id} found in DB but not in active memory. Proceeding with deactivation.")

    # Schedule cleanup to happen in the background
    # The cleanup_session function will handle resource release and database deactivation
    background_tasks.add_task(cleanup_session, session_id)
    
    # Determine current active sessions *before* cleanup potentially finishes
    # This part remains tricky as the session might be removed by the background task immediately.
    # We filter the list based on the current state, excluding the one being deleted.
    current_active_sessions = list(active_agents.keys())
    if session_id in current_active_sessions:
         # Exclude the session being deleted if it's still in the in-memory dicts
         # Note: This is a snapshot, the background task might remove it shortly after.
        current_active_sessions.remove(session_id)

    return StatusResponse(
        status="cleanup_scheduled",
        active_sessions=current_active_sessions,
        message=f"Session {session_id} scheduled for cleanup"
    )

@app.get("/sessions", response_model=StatusResponse, tags=["Sessions"])
async def get_sessions():
    """
    Get all active sessions
    
    - Returns a list of all active session IDs
    - Includes chatbot sessions
    """
    # Get active sessions from database
    db_sessions = await db.get_active_sessions()
    session_ids = [session["session_id"] for session in db_sessions]
    
    return StatusResponse(
        status="ok",
        active_sessions=session_ids
    )

@app.get("/chat/history/{session_id}", response_model=ChatHistoryResponse, tags=["Sessions"])
async def get_chat_history(
    session_id: str, 
    limit: int = 100, 
    offset: int = 0,
    role: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get chat history for a session
    
    - Returns messages exchanged in the specified session
    - Can be filtered by role ('user' or 'assistant')
    - Can be filtered by date range
    - Supports pagination with limit and offset parameters
    
    Args:
        session_id: Unique identifier for the session
        limit: Maximum number of messages to return (default: 100)
        offset: Number of messages to skip for pagination (default: 0)
        role: Filter messages by role ('user' or 'assistant'), if provided
        start_date: Filter messages after this date (format: YYYY-MM-DD)
        end_date: Filter messages before this date (format: YYYY-MM-DD)
    """
    # Check if session exists
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Get chat history with filters
    history = await db.get_filtered_chat_history(
        session_id=session_id,
        limit=limit,
        offset=offset,
        role=role,
        start_date=start_date,
        end_date=end_date
    )
    
    return ChatHistoryResponse(
        session_id=session_id,
        history=history,
        count=len(history)
    )

if __name__ == "__main__":
    # Start the FastAPI server and frontend
    start_server()
