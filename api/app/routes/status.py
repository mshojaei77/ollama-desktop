from fastapi import APIRouter
from app.core.chatbot_manager import ChatbotManager
from app.core.lifecycle import get_active_mcp_clients

manager = ChatbotManager()

router = APIRouter(tags=["Status"])

@router.get("/")
async def root():
    """Root endpoint providing API status information"""
    active_mcp_clients = get_active_mcp_clients()
    
    return {
        "status": "ok",
        "service": "Ollama API",
        "active_sessions": len(manager.get_chatbots()),
        "mcp_servers": {
            "active_count": len(active_mcp_clients),
            "active_servers": list(active_mcp_clients.keys())
        }
    }