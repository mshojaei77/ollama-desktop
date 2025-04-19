from app.core.chatbot_manager import ChatbotManager
from app.database import database as db
from .logger import app_logger

manager = ChatbotManager()

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return f"session-{uuid.uuid4()}"

async def cleanup_session(session_id: str):
    """Clean up resources for a session"""
    # 1. Clean up in-memory resources chatbots
    chatbot = manager.get_chatbot(session_id)
    if chatbot:
        await chatbot.cleanup()
        manager.delete_chatbot(session_id)
        app_logger.info(f"Cleaned up chatbot session: {session_id}")
    
    # 2. Permanently delete session and history from the database
    try:
        await db.delete_session_permanently(session_id)
    except Exception as e:
        app_logger.error(f"Error permanently deleting session {session_id} from database: {str(e)}")

