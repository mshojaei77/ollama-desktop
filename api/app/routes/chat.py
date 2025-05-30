from fastapi import APIRouter, HTTPException, Form
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
from app.core.chatbot import OllamaMCPPackage, app_logger
from app.database import database as db
from app.schemas.chat import (
    InitializeRequest,
    InitializeResponse,
    ChatRequest,
    ChatResponse,
    ChatHistoryResponse,
    AvailableChatsResponse,
    ChatSession
)
from app.core.chatbot_manager import ChatbotManager
from app.utils.helper import generate_session_id
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any, AsyncGenerator

router = APIRouter(prefix="/chat", tags=["Chat"])
manager = ChatbotManager()

@router.post("/initialize", response_model=InitializeResponse, tags=["Chat"])
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
        chatbot = manager.get_chatbot(session_id)
        if chatbot:
            await chatbot.cleanup()
            manager.remove_chatbot(session_id)
        
        # Log the initialization attempt with the model name
        app_logger.info(f"Initializing chatbot with model: {request.model_name}")
        
        # Create new chatbot
        chatbot = await OllamaMCPPackage.create_standalone_chatbot(
            model_name=request.model_name,
            system_message=request.system_message
        )
        
        # Store in active sessions
        manager.add_chatbot(session_id, chatbot)
        
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

@router.post("/message/", tags=["Chat"])
async def chat_message_stream(request: ChatRequest):
    """
    Send a message to a chatbot and stream the response using SSE
    
    - Requires a valid session_id from a previous /chat/initialize call
    - Returns a streaming response from the model
    - Always tries MCP functionality first if available
    - Saves the conversation history to the database once completed
    """
    # Check if session exists in active chatbots
    chatbot = manager.get_chatbot(request.session_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response using MCP tools when available"""
        try:            
            # Save user message to history
            await db.add_chat_message(request.session_id, "user", request.message)
            
            # Set up variables to collect the full response
            full_response = []
            tools = []
            
            # Log the request to help with debugging
            app_logger.info(f"Starting stream for message: {request.message[:50]}...")
            
            chatbot = manager.get_chatbot(request.session_id)

            if chatbot:
                app_logger.info(f"Using chatbot for session {request.session_id}")
                
                # Process query with MCP tools and stream the response
                async for chunk in chatbot.chat(request.message):
                    if chunk is None:
                        break
                        
                    try:
                        print("! chunk", chunk)
                        chunk_data = json.loads(chunk.replace('data: ', ''))
                    except json.JSONDecodeError as e:
                        app_logger.error(f"JSON decode error: {str(e)}. Chunk: {chunk}")
                        continue  # Skip this chunk and continue with the next one
                    
                    if chunk_data['type'] == 'token':
                        if isinstance(chunk_data['response'], str):
                            full_response.append(chunk_data['response'])
                        else:
                            app_logger.error(f"Unexpected type in full_response: {type(chunk_data['response'])}, value: {chunk_data['response']}")
                            full_response.append(str(chunk_data['response']))
                        yield chunk
                    elif chunk_data['type'] == 'tool':
                        tools.append(chunk_data)
                        yield chunk
                
                print('! tools', tools)
            
            # Combine the full response for logging
            complete_response = ''.join(full_response)
            
            # Log the complete response
            if complete_response:
                app_logger.info(f"Streamed complete response: {complete_response[:100]}...")
            else:
                app_logger.warning("No content received in stream - empty response")
                # Add a fallback response if nothing was streamed
                fallback_response = "I'm sorry, I couldn't generate a response. There might be an issue with the model."
                yield f"data: {json.dumps({'text': fallback_response})}\n\n"
                complete_response = fallback_response
            
            # Update session activity
            await db.update_session_activity(request.session_id)
            
            # Save assistant response to history (with tools if MCP was used)
            await db.add_chat_message(request.session_id, "assistant", complete_response, tools=tools)
            
            # Send completion signal
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            app_logger.error(f"Error streaming chat message: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse, tags=["Sessions"])
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


@router.get("/all", response_model=AvailableChatsResponse, tags=["Sessions"])
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

@router.get("/chats/search", response_model=AvailableChatsResponse, tags=["Sessions"])
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

# Add Vision Chat endpoint
@router.post("/vision", response_model=ChatResponse, tags=["Chat"])
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
    # Retrieve chatbot instance
    chatbot = manager.get_chatbot(session_id)   
    if not chatbot:
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
        response_content = await chatbot.chat_with_image(message, temp_image_paths)
    # Save assistant response
    await db.add_chat_message(session_id, "assistant", response_content)
    await db.update_session_activity(session_id)
    return ChatResponse(response=response_content, session_id=session_id)
