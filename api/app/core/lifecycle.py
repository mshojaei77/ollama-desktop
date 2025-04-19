import subprocess
import sys
from app.database import database as db
from app.core.chatbot import app_logger
from app.services.agents.registry import agent_registry

async def startup_event():
    """Initialize the database and agents on application startup"""
    db.init_db()
    db.migrate_database()
    app_logger.info("Database initialized and migrated")
    
    # Initialize the agent registry
    await agent_registry.initialize()
    # Simplify this logging to avoid recursion issues
    app_logger.info("Agent registry initialized")
    
    # Start Ollama on Windows platforms
    if sys.platform.startswith('win'):
        try:
            subprocess.Popen(['powershell', '-Command', 'ollama list'], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            app_logger.error(f"Failed to start Ollama: {str(e)}")

async def shutdown_event():
    """Clean up resources on application shutdown"""
    app_logger.info("Shutting down application, cleaning up resources...")
    
    # Clean up agent registry resources
    await agent_registry.cleanup()
    app_logger.info("Agent registry cleaned up")