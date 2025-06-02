import subprocess
import sys
from app.database import database as db
from app.core.chatbot import app_logger, OllamaMCPPackage, MCPClient
from app.services.agents.registry import agent_registry
from typing import Dict, Any

# Global dictionary to store active MCP clients
active_mcp_clients: Dict[str, MCPClient] = {}

async def startMCPServers() -> Dict[str, MCPClient]:
    """
    Start all active MCP servers from configuration
    
    Returns:
        dict: Dictionary of server_name -> MCPClient for successfully started servers
    """
    global active_mcp_clients
    
    try:
        app_logger.info("Starting MCP servers...")
        
        # Load MCP configuration
        config = await OllamaMCPPackage.load_mcp_config()
        if not config or "mcpServers" not in config:
            app_logger.info("No MCP servers configured")
            return {}
        
        servers_config = config.get("mcpServers", {})
        started_servers = {}
        
        for server_name, server_config in servers_config.items():
            try:
                # Check if server is active (default to True if not specified)
                if not server_config.get("active", True):
                    app_logger.info(f"Skipping inactive MCP server: {server_name}")
                    continue
                
                app_logger.info(f"Starting MCP server: {server_name}")
                
                # Create MCP client
                client = await OllamaMCPPackage.create_client(model_name="llama3.2")
                
                # Connect to server based on type
                server_type = server_config.get("type", "stdio")
                success = False
                
                if server_type == "sse":
                    server_url = server_config.get("url")
                    if not server_url:
                        app_logger.error(f"Server {server_name}: URL required for SSE server")
                        continue
                    
                    success = await client.connect_to_sse_server(server_url)
                    
                elif server_type == "stdio":
                    command = server_config.get("command")
                    args = server_config.get("args", [])
                    
                    if not command:
                        app_logger.error(f"Server {server_name}: Command required for STDIO server")
                        continue
                    
                    success = await client.connect_to_stdio_server(command, args)
                    
                else:
                    app_logger.error(f"Server {server_name}: Unsupported server type: {server_type}")
                    continue
                
                if success:
                    started_servers[server_name] = client
                    active_mcp_clients[server_name] = client
                    app_logger.info(f"Successfully started MCP server: {server_name}")
                else:
                    app_logger.error(f"Failed to start MCP server: {server_name}")
                    await client.cleanup()
                    
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
    global active_mcp_clients
    
    app_logger.info("Cleaning up MCP server connections...")
    
    for server_name, client in active_mcp_clients.items():
        try:
            await client.cleanup()
            app_logger.info(f"Cleaned up MCP server: {server_name}")
        except Exception as e:
            app_logger.error(f"Error cleaning up MCP server {server_name}: {str(e)}")
    
    active_mcp_clients.clear()
    app_logger.info("MCP server cleanup completed")

def get_active_mcp_clients() -> Dict[str, MCPClient]:
    """Get the currently active MCP clients"""
    return active_mcp_clients.copy()

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