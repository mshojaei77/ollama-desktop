import subprocess
import sys
from app.database import database as db
from app.utils.logger import app_logger
from app.core.mcp.client import MCPClient
from app.core.mcp.manager import MCPClientManager
from app.core.mcp.servers import MCPServersConfig
from app.services.agents.registry import agent_registry
from typing import Dict, Any

async def startMCPServers() -> Dict[str, MCPClient]:
    """
    Start all active MCP servers from configuration
    
    Returns:
        dict: Dictionary of server_name -> MCPClient for successfully started servers
    """
    mcp_manager = MCPClientManager()
    
    try:
        mcp_servers_config = MCPServersConfig()
        app_logger.info("Starting MCP servers...")
        
        # Load MCP configuration
        servers_config = mcp_servers_config.get_mcp_servers()
        started_servers = {}
        
        for server_name, server_config in servers_config.items():
            try:
                # Check if server is active (default to True if not specified)
                if not server_config.get("active", True):
                    app_logger.info(f"Skipping inactive MCP server: {server_name}")
                    continue
                
                app_logger.info(f"Starting MCP server: {server_name}")
                
                # Create MCP client
                client = await MCPClient.from_config(server_name, server_config)

                if not client:
                    app_logger.error(f"Failed to start MCP server: {server_name}")
                    continue

                started_servers[server_name] = client
                mcp_manager.add_mcp_client(server_name, client)
                app_logger.info(f"Successfully started MCP server: {server_name}")
                    
            except Exception as e:
                app_logger.error(f"Error starting MCP server {server_name}: {str(e)}")
                continue
        
        app_logger.info(f"Started {len(started_servers)} MCP servers: {list(started_servers.keys())}")
        return started_servers
        
    except Exception as e:
        app_logger.error(f"Error in startMCPServers: {str(e)}")
        return {}

async def cleanup_mcp_servers():
    """Clean up all active MCP server connections"""
    mcp_manager = MCPClientManager()
    
    app_logger.info("Cleaning up MCP server connections...")
    
    await mcp_manager.cleanup_all_mcp_clients()
    app_logger.info("MCP server cleanup completed")

def get_active_mcp_clients() -> Dict[str, MCPClient]:
    """Get the currently active MCP clients"""
    mcp_manager = MCPClientManager()
    return mcp_manager.get_mcp_clients()

async def startup_event():
    """Initialize the database and agents on application startup"""
    db.init_db()
    db.migrate_database()
    app_logger.info("Database initialized and migrated")
    
    # Initialize the agent registry
    await agent_registry.initialize()
    # Simplify this logging to avoid recursion issues
    app_logger.info("Agent registry initialized")
    
    # Start MCP servers
    await startMCPServers()
    
    # Start Ollama on Windows platforms
    if sys.platform.startswith('win'):
        try:
            subprocess.Popen(['powershell', '-Command', 'ollama list'], creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            app_logger.error(f"Failed to start Ollama: {str(e)}")

async def shutdown_event():
    """Clean up resources on application shutdown"""
    app_logger.info("Shutting down application, cleaning up resources...")
    
    # Clean up MCP servers
    await cleanup_mcp_servers()
    
    # Clean up agent registry resources
    await agent_registry.cleanup()
    app_logger.info("Agent registry cleaned up")