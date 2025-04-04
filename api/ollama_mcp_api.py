"""
Ollama MCP API - Integration example with FastAPI
"""

import os
import json
import asyncio
import webbrowser  # Add this import
import threading
import time
from typing import Dict, List, Optional, Any, Union, AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ollama_mcp import OllamaMCPPackage, OllamaChatbot, MCPClient, app_logger
import db  # Import our new database module
from config_io import read_ollama_config, write_ollama_config

# Initialize FastAPI app
app = FastAPI(
    title="Ollama MCP API",
    description="API for interacting with Ollama models and MCP tools",
    version="1.0.0",
    docs_url="/docs",              # Explicitly set Swagger UI endpoint (default)
    redoc_url="/redoc",            # Also enable ReDoc (alternative docs)
    openapi_url="/openapi.json",   # URL for the OpenAPI schema
    openapi_tags=[
        {
            "name": "Chat",
            "description": "Operations for working with standalone Ollama chatbots"
        },
        {
            "name": "MCP",
            "description": "Operations for working with MCP-enabled clients and tools"
        },
        {
            "name": "Sessions",
            "description": "Operations for managing sessions and retrieving chat history"
        },
        {
            "name": "Models",
            "description": "Operations for getting information about available models"
        }
    ]
)

# Global state for clients and chatbots
active_clients: Dict[str, MCPClient] = {}
active_chatbots: Dict[str, OllamaChatbot] = {}


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

class MCPServerConnectRequest(BaseModel):
    server_type: str  # "sse" or "stdio"
    server_url: Optional[str] = None  # For SSE
    command: Optional[str] = None     # For STDIO
    args: Optional[List[str]] = None  # For STDIO
    session_id: Optional[str] = None
    model_name: str = "llama3.2"

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

class MCPServerAddRequest(BaseModel):
    server_name: str
    server_type: str = "stdio"  # "sse" or "stdio"
    command: Optional[str] = None  # For STDIO
    args: Optional[List[str]] = None  # For STDIO
    server_url: Optional[str] = None  # For SSE


# ----- Helper Functions -----

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return f"session-{uuid.uuid4()}"

async def cleanup_session(session_id: str):
    """Clean up resources for a session"""
    if session_id in active_clients:
        await active_clients[session_id].cleanup()
        del active_clients[session_id]
        app_logger.info(f"Cleaned up client session: {session_id}")
        
    if session_id in active_chatbots:
        await active_chatbots[session_id].cleanup()
        del active_chatbots[session_id]
        app_logger.info(f"Cleaned up chatbot session: {session_id}")
    
    # Mark session as inactive in database
    await db.deactivate_session(session_id)


# ----- API Endpoints -----

@app.get("/", tags=["Status"])
async def root():
    """Root endpoint providing API status information"""
    return {
        "status": "ok",
        "service": "Ollama MCP API",
        "active_sessions": len(active_clients) + len(active_chatbots)
    }

@app.on_event("startup")
async def startup_event():
    """Initialize the database on application startup"""
    db.init_db()
    db.migrate_database()
    app_logger.info("Database initialized and migrated")
    
    # Start Ollama on Windows platforms
    import sys
    import subprocess
    if sys.platform.startswith('win'):
        try:
            subprocess.Popen(['powershell', '-Command', 'ollama list'], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            app_logger.error(f"Failed to start Ollama: {str(e)}")

@app.post("/chat/initialize", response_model=InitializeResponse, tags=["Chat"])
async def initialize_chatbot(request: InitializeRequest):
    """
    Initialize a standalone Ollama chatbot
    
    - Creates a new chatbot with the specified model
    - Returns a session ID for subsequent interactions
    - Optionally accepts a system message to customize the chatbot's behavior
    """
    try:
        # Validate model name is not empty
        if not request.model_name or request.model_name.strip() == "":
            raise HTTPException(status_code=400, detail="Model name cannot be empty")
        
        session_id = request.session_id or generate_session_id()
        
        # Clean up existing session if it exists
        if session_id in active_chatbots:
            await cleanup_session(session_id)
        
        # Log the initialization attempt with the model name
        app_logger.info(f"Initializing chatbot with model: {request.model_name}")
        
        # Create new chatbot
        chatbot = await OllamaMCPPackage.create_standalone_chatbot(
            model_name=request.model_name,
            system_message=request.system_message
        )
        
        # Store in active sessions
        active_chatbots[session_id] = chatbot
        
        # Save to database
        await db.create_session(
            session_id=session_id,
            model_name=request.model_name,
            session_type="chatbot",
            system_message=request.system_message
        )
        
        return InitializeResponse(
            session_id=session_id,
            status="ready",
            model=request.model_name
        )
    except ValueError as e:
        # Handle specific value errors
        app_logger.error(f"Value error initializing chatbot: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly so FastAPI handles them correctly
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error initializing chatbot: {str(e)}", exc_info=True)
        # Handle other unexpected errors as 500
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/message", response_model=ChatResponse, tags=["Chat"])
async def chat_message(request: ChatRequest):
    """
    Send a message to a chatbot
    
    - Requires a valid session_id from a previous /chat/initialize call
    - Returns the model's response to the user message
    - Saves the conversation history to the database
    """
    if request.session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        chatbot = active_chatbots[request.session_id]
        
        # Save user message to history
        await db.add_chat_message(request.session_id, "user", request.message)
        
        # Get response from chatbot
        response = await chatbot.chat(request.message)
        
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
    Send a message to a chatbot and stream the response using SSE
    
    - Requires a valid session_id from a previous /chat/initialize call
    - Returns a streaming response from the model
    - Saves the conversation history to the database once completed
    """
    if request.session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response from Ollama"""
        try:
            chatbot = active_chatbots[request.session_id]
            
            # Save user message to history
            await db.add_chat_message(request.session_id, "user", request.message)
            
            # Set up variables to collect the full response
            full_response = []
            
            # Use the chatbot's streaming method to get chunks directly from Ollama
            async for chunk in chatbot.chat_stream(request.message):
                if chunk is None:
                    # This is the completion signal from chat_stream
                    break
                
                # Add to the full response
                full_response.append(chunk)
                
                # Send the chunk as an SSE event
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            
            # Combine the full response for logging (the message is already saved by chat_stream)
            complete_response = ''.join(full_response)
            app_logger.info(f"Streamed complete response: {complete_response[:100]}...")
            
            # Update session activity
            await db.update_session_activity(request.session_id)
            
            # Save assistant response to history
            await db.add_chat_message(request.session_id, "assistant", complete_response)
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            app_logger.error(f"Error streaming chat message: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )

@app.post("/mcp/connect", response_model=InitializeResponse, tags=["MCP"])
async def connect_to_mcp(request: MCPServerConnectRequest):
    """
    Connect to an MCP server
    
    - Supports both SSE and STDIO server types
    - Creates a new MCP client with the specified model
    - Returns a session ID for subsequent interactions
    """
    try:
        session_id = request.session_id or generate_session_id()
        
        # Clean up existing session if it exists
        if session_id in active_clients:
            await cleanup_session(session_id)
        
        # Create MCP client
        client = await OllamaMCPPackage.create_client(model_name=request.model_name)
        
        # Connect to server based on type
        if request.server_type == "sse":
            if not request.server_url:
                raise HTTPException(status_code=400, detail="server_url is required for SSE connections")
            
            await client.connect_to_sse_server(server_url=request.server_url)
        
        elif request.server_type == "stdio":
            if not request.command or not request.args:
                raise HTTPException(status_code=400, detail="command and args are required for STDIO connections")
            
            await client.connect_to_stdio_server(command=request.command, args=request.args)
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported server type: {request.server_type}")
        
        # Store in active clients
        active_clients[session_id] = client
        
        # Save to database
        await db.create_session(
            session_id=session_id,
            model_name=request.model_name,
            session_type="mcp_client"
        )
        
        return InitializeResponse(
            session_id=session_id,
            status="connected",
            model=request.model_name
        )
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly so FastAPI handles them correctly
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error connecting to MCP server: {str(e)}")
        # Handle other unexpected errors as 500
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/mcp/query", response_model=ChatResponse)
async def process_mcp_query(request: ChatRequest):
    """Process a query with MCP tools"""
    if request.session_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        client = active_clients[request.session_id]
        
        # Process query
        response = await client.process_query(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing MCP query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing MCP query: {str(e)}")

@app.post("/mcp/direct-query", response_model=ChatResponse)
async def process_direct_query(request: ChatRequest):
    """Process a direct query with Ollama (no MCP tools)"""
    if request.session_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        client = active_clients[request.session_id]
        
        # Set direct mode
        client.direct_mode = True
        
        # Process direct query
        response = await client.process_direct_query(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing direct query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing direct query: {str(e)}")

@app.get("/available-models", tags=["Models"])
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

@app.get("/mcp/servers")
async def get_mcp_servers():
    """Get list of configured MCP servers"""
    try:
        config = await OllamaMCPPackage.load_mcp_config()
        return {"servers": config.get("mcpServers", {})}
    except Exception as e:
        app_logger.error(f"Error getting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP servers: {str(e)}")

@app.post("/mcp/servers", tags=["MCP"])
async def add_mcp_server(request: MCPServerAddRequest):
    """
    Add a new MCP server configuration
    
    - Adds a new server to the ollama_desktop_config.json file
    - Supports both SSE and STDIO server types
    - Returns updated list of configured servers
    
    Args:
        request: Server configuration details
    """
    try:
        # Validate the request based on server_type
        if request.server_type == "sse":
            if not request.server_url:
                raise HTTPException(
                    status_code=400, 
                    detail="server_url is required for SSE server type"
                )
        elif request.server_type == "stdio":
            if not request.command:
                raise HTTPException(
                    status_code=400, 
                    detail="command is required for STDIO server type"
                )
            if not request.args or not isinstance(request.args, list):
                raise HTTPException(
                    status_code=400, 
                    detail="args must be a non-empty list for STDIO server type"
                )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported server type: {request.server_type}. Must be 'sse' or 'stdio'."
            )
        
        # Load current configuration
        config = await OllamaMCPPackage.load_mcp_config()
        
        if not config:
            config = {"mcpServers": {}}
        elif "mcpServers" not in config:
            config["mcpServers"] = {}
            
        # Check if server name already exists
        if request.server_name in config["mcpServers"]:
            raise HTTPException(
                status_code=409, 
                detail=f"Server with name '{request.server_name}' already exists"
            )
            
        # Add new server configuration based on type
        if request.server_type == "sse":
            config["mcpServers"][request.server_name] = {
                "type": "sse",
                "url": request.server_url
            }
        else:  # stdio
            config["mcpServers"][request.server_name] = {
                "type": "stdio",
                "command": request.command,
                "args": request.args
            }
            
        # Write updated configuration
        success = await write_ollama_config(config)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to write configuration file"
            )
            
        # Return updated list of servers
        return {"servers": config["mcpServers"], "message": f"Server '{request.server_name}' added successfully"}
        
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error adding MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding MCP server: {str(e)}")

@app.delete("/sessions/{session_id}", response_model=StatusResponse)
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """Delete a session"""
    if session_id not in active_clients and session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Schedule cleanup to happen in the background
    # The cleanup_session function will handle resource release and database deactivation
    background_tasks.add_task(cleanup_session, session_id)
    
    # Determine current active sessions *before* cleanup potentially finishes
    current_active_sessions = list(set(list(active_clients.keys()) + list(active_chatbots.keys())))
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
    - Includes both chatbot and MCP client sessions
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
    print(f"Chat history: {history}")
    
    return ChatHistoryResponse(
        session_id=session_id,
        history=history,
        count=len(history)
    )

@app.get("/models/recent")
async def get_recent_models(limit: int = 5):
    """Get recently used models"""
    try:
        models = await db.get_recently_used_models(limit)
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting recent models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting recent models: {str(e)}")

@app.get("/models")
async def get_models(sort_by: Optional[str] = None):
    """
    Get all available models, ensuring the database is updated with models
    currently available in Ollama, sorted by specified criteria.
    
    Optional query parameter:
    - sort_by: 'last_used' to sort by most recently used, 'name' for alphabetical
    """
    try:
        app_logger.info(f"Getting models with sort_by={sort_by}")
        
        # 1. Get currently available models from Ollama
        available_models = await OllamaMCPPackage.get_available_models()
        app_logger.info(f"Available models from Ollama: {available_models}")
        
        # 2. Try to ensure each available model exists in the database
        # But continue even if this part fails (especially for tests with mocks)
        if available_models:
            try:
                for model_info in available_models:
                    # Assuming get_available_models returns a list of dicts with a 'name' key
                    # or a list of strings (handle both formats)
                    model_name = model_info.get('name') if isinstance(model_info, dict) else model_info
                    if model_name:
                        await db.ensure_model_exists(model_name)
            except Exception as db_error:
                # Log but don't fail completely - this handles mock issues in tests
                app_logger.warning(f"Could not update models in database: {str(db_error)}. Continuing with available models.")
                    
        # 3. Get models from the database with sorting if possible
        try:
            models = await db.get_models(sort_by)
            app_logger.info(f"Models from database: {models}")
        except Exception as db_error:
            # If database retrieval fails, fall back to direct model list
            app_logger.warning(f"Could not retrieve sorted models from database: {str(db_error)}. Using available models directly.")
            # Convert to format expected in the response
            models = []
            for model_info in available_models:
                if isinstance(model_info, dict):
                    models.append(model_info)
                else:
                    models.append({"name": model_info, "last_used": None})
        
        return {"models": models}
        
    except Exception as e:
        app_logger.error(f"Error getting models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

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

@app.get("/mcp/servers/active", tags=["MCP"])
async def get_active_mcp_servers():
    """Get list of active MCP servers"""
    try:
        # Get list of active servers from database
        active_servers = await db.get_active_mcp_servers()
        return {"active_servers": active_servers}
    except Exception as e:
        app_logger.error(f"Error getting active MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting active MCP servers: {str(e)}")

@app.post("/mcp/servers/toggle-active/{server_name}", tags=["MCP"])
async def toggle_mcp_server_active(server_name: str, active: bool):
    """Activate or deactivate an MCP server"""
    try:
        # Update server active status in database
        success = await db.set_mcp_server_active(server_name, active)
        if not success:
            raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
        
        # Get updated list of active servers
        active_servers = await db.get_active_mcp_servers()
        return {"active": active, "server_name": server_name, "active_servers": active_servers}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error toggling MCP server active status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error toggling MCP server active status: {str(e)}")

@app.post("/chat/initialize-with-mcp", response_model=InitializeResponse, tags=["Chat"])
async def initialize_chat_with_mcp(request: InitializeRequest):
    """
    Initialize a chat with active MCP servers if available, otherwise create a regular chat
    
    - Checks for active MCP servers
    - If active servers exist, creates a chat with MCP integration
    - If no active servers, falls back to regular chat
    """
    try:
        # Validate model name is not empty
        if not request.model_name or request.model_name.strip() == "":
            raise HTTPException(status_code=400, detail="Model name cannot be empty")
        
        session_id = request.session_id or generate_session_id()
        
        # Clean up existing session if it exists
        if session_id in active_chatbots or session_id in active_clients:
            await cleanup_session(session_id)
        
        # Get active MCP servers
        active_servers = await db.get_active_mcp_servers()
        
        # If there are active MCP servers, use them
        if active_servers:
            app_logger.info(f"Initializing chat with active MCP servers: {active_servers}")
            
            # Get the first active server config for now (in future could support multiple)
            server_config = await OllamaMCPPackage.get_mcp_server_config(active_servers[0])
            
            if not server_config:
                app_logger.warning(f"No config found for active server {active_servers[0]}, falling back to regular chat")
                return await initialize_chatbot(request)
            
            # Create MCP client
            client = await OllamaMCPPackage.create_client(model_name=request.model_name)
            
            # Connect to server based on type
            server_type = server_config.get('type', 'stdio')
            
            if server_type == "sse":
                server_url = server_config.get('url')
                if not server_url:
                    raise HTTPException(status_code=400, detail="Server URL not found in config")
                
                await client.connect_to_sse_server(server_url=server_url)
            
            elif server_type == "stdio":
                command = server_config.get('command')
                args = server_config.get('args', [])
                
                if not command:
                    raise HTTPException(status_code=400, detail="Command not found in config")
                
                await client.connect_to_stdio_server(command=command, args=args)
            
            # Store in active clients
            active_clients[session_id] = client
            
            # Save to database
            await db.create_session(
                session_id=session_id,
                model_name=request.model_name,
                session_type="mcp_client",
                system_message=request.system_message
            )
            
            return InitializeResponse(
                session_id=session_id,
                status="connected_with_mcp",
                model=request.model_name
            )
        else:
            # No active MCP servers, fall back to regular chat
            app_logger.info("No active MCP servers, initializing regular chat")
            return await initialize_chatbot(request)
            
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error initializing chat with MCP: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ----- Programmatic API Examples -----

async def example_standalone():
    """Example of using the package with standalone Ollama (no MCP)"""
    # Create a standalone chatbot
    chatbot = await OllamaMCPPackage.create_standalone_chatbot(
        model_name="llama3.2",
        system_message="You are a helpful assistant who speaks like a pirate.",
        temperature=0.8
    )
    
    try:
        # Chat with the model
        response = await chatbot.chat("Tell me about neural networks.")
        print(f"Chatbot: {response}")
        
        # Continue the conversation
        response = await chatbot.chat("Summarize what you just told me.")
        print(f"Chatbot: {response}")
    finally:
        # Clean up when done
        await chatbot.cleanup()

async def example_with_mcp():
    """Example of using the package with MCP tools"""
    # Create an MCP client
    client = await OllamaMCPPackage.create_client()
    
    try:
        # Connect to an SSE server
        await client.connect_to_sse_server("http://localhost:3000/sse")
        
        # Process a query
        response = await client.process_query("What's the weather in Paris?")
        print(f"Response: {response}")
    finally:
        # Clean up when done
        await client.cleanup()


# ----- Main Function -----

def open_browser():
    """Open browser after a short delay to ensure server is up"""
    time.sleep(1.5)  # Wait for server to start
    webbrowser.open("http://localhost:8000/docs")

def start_server():
    """Start the FastAPI server and open Swagger UI"""
    # Start browser in a separate thread so it doesn't block the server
    threading.Thread(target=open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Start the FastAPI server with auto-opening browser
    start_server()    
    # Examples of programmatic usage are defined above
    # To run them directly:
    # asyncio.run(example_standalone())
    # asyncio.run(example_with_mcp())
