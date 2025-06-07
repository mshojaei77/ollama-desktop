"""
MCP Agents Package

This package contains the MCP (Model Context Protocol) agents system for Ollama Desktop.
MCP Agents are customizable agents that leverage MCP servers to interact with external systems.
"""

import logging

# Configure logging for MCP agents
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

from .models import MCPAgentConfig, MCPAgent, MCPAgentListResponse
from .service import MCPAgentService
from .routes import router as mcp_agents_router

__all__ = ["MCPAgentConfig", "MCPAgent", "MCPAgentListResponse", "MCPAgentService", "mcp_agents_router"] 