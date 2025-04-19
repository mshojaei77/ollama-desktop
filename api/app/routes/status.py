from fastapi import APIRouter
from app.core.chatbot_manager import ChatbotManager

manager = ChatbotManager()

router = APIRouter(tags=["Status"])

@router.get("/")
async def root():
    """Root endpoint providing API status information"""
    return {
        "status": "ok",
        "service": "Ollama API",
        "active_sessions": len(manager.get_chatbots())
    }