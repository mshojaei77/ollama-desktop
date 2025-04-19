from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.core.chatbot import Chatbot
from app.database import database as db
from app.utils.logger import app_logger
from app.schemas.chat import StatusResponse
from typing import Optional
from app.core.chatbot_manager import ChatbotManager
from app.utils.helper import cleanup_session
from app.core.config import get_allowed_upload_extensions
import tempfile
from pathlib import Path
from fastapi import UploadFile, File
import shutil

router = APIRouter(prefix="/sessions", tags=["Sessions"])
manager = ChatbotManager()
@router.delete("/{session_id}", response_model=StatusResponse)
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """Delete a session"""
    chatbot = manager.get_chatbot(session_id)
    
    # Check if session exists in memory or database
    if not chatbot:
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
    current_active_sessions = list(set(list(manager.get_chatbots().keys())))
    if session_id in current_active_sessions:
         # Exclude the session being deleted if it's still in the in-memory dicts
         # Note: This is a snapshot, the background task might remove it shortly after.
        current_active_sessions.remove(session_id)

    return StatusResponse(
        status="cleanup_scheduled",
        active_sessions=current_active_sessions,
        message=f"Session {session_id} scheduled for cleanup"
    )

@router.get("/", response_model=StatusResponse, tags=["Sessions"])
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



@router.post("/{session_id}/upload_file", tags=["Context"])
async def upload_file_to_session(session_id: str, file: UploadFile = File(...)):
    """
    Upload a file (.txt, .md, .pdf) to add its content as context to a session.

    - Validates the session ID and file type.
    - Saves the file temporarily.
    - Processes the file content and adds it to the session's vector store.
    - Cleans up the temporary file.
    """
    chatbot: Optional[Chatbot] = None

    # Check if session exists in active_chatbots
    chatbot = manager.get_chatbot(session_id)
    if not chatbot:
        # Verify if the session exists in the database but isn't active in memory
        db_session = await db.get_session(session_id)
        if db_session:
             # Session exists but isn't loaded. We could potentially load it here,
             # but for simplicity, let's require it to be active.
             # Or, we could decide to initialize it on the fly if needed.
             raise HTTPException(status_code=404, detail=f"Session {session_id} exists but is not currently active. Please initialize it first.")
        else:
             raise HTTPException(status_code=404, detail=f"Session {session_id} not found.")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in get_allowed_upload_extensions():
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed extensions are: {', '.join(get_allowed_upload_extensions())}"
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

        # Process the file using the chatbot's method
        try:
            await chatbot.add_file_context(temp_file_path, file.filename)
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
