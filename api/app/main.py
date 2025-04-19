"""
Ollama MCP API - Integration example with FastAPI
run with: uvicorn main:app --reload
or python -m uvicorn main:app --reload
"""

from fastapi import FastAPI
from app.core.config import configure_middleware, get_app_settings
from app.core.lifecycle import startup_event, shutdown_event
from app.routes.chat import router as chat_router
from app.routes.agents import router as agents_router
from app.routes.mcp import router as mcp_router
from app.routes.sessions import router as sessions_router
from app.routes.status import router as status_router

# Initialize FastAPI app
app = FastAPI(**get_app_settings())

# Configure middleware
configure_middleware(app)

# Include routers
app.include_router(status_router)
app.include_router(agents_router)
app.include_router(chat_router)
app.include_router(mcp_router)
app.include_router(sessions_router)

# Register lifecycle events
app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)