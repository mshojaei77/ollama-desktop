from app.core.chatbot import OllamaMCPPackage, app_logger
from app.database import database as db
from app.schemas.mcp import MCPServerAddRequest
from fastapi import APIRouter, HTTPException
from app.core.chatbot_manager import ChatbotManager
from app.core.lifecycle import get_active_mcp_clients, startMCPServers, cleanup_mcp_servers

router = APIRouter(prefix="/mcp", tags=["MCP"])
manager = ChatbotManager()

@router.get("/servers")
async def get_mcp_servers():
    """Get list of configured MCP servers"""
    try:
        config = await OllamaMCPPackage.load_mcp_config()
        return {"servers": config.get("mcpServers", {})}
    except Exception as e:
        app_logger.error(f"Error getting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP servers: {str(e)}")

@router.post("/servers", tags=["MCP"])
async def add_mcp_server(request: MCPServerAddRequest):
    """
    Add a new MCP server configuration
    
    - Adds a new server to the ollama_desktop_config.json file
    - Supports both SSE and STDIO server types
    - Returns updated list of configured servers
    
    Args:
        request: Server configuration details
    """
    try:
        # Validate the request based on server_type
        if request.server_type == "sse":
            if not request.server_url:
                raise HTTPException(
                    status_code=400, 
                    detail="server_url is required for SSE server type"
                )
        elif request.server_type == "stdio":
            if not request.command:
                raise HTTPException(
                    status_code=400, 
                    detail="command is required for STDIO server type"
                )
            if not request.args or not isinstance(request.args, list):
                raise HTTPException(
                    status_code=400, 
                    detail="args must be a non-empty list for STDIO server type"
                )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported server type: {request.server_type}. Must be 'sse' or 'stdio'."
            )
        
        # Load current configuration
        config = await OllamaMCPPackage.load_mcp_config()
        
        if not config:
            config = {"mcpServers": {}}
        elif "mcpServers" not in config:
            config["mcpServers"] = {}
            
        # Check if server name already exists
        if request.server_name in config["mcpServers"]:
            raise HTTPException(
                status_code=409, 
                detail=f"Server with name '{request.server_name}' already exists"
            )
            
        # Add new server configuration based on type
        if request.server_type == "sse":
            config["mcpServers"][request.server_name] = {
                "type": "sse",
                "url": request.server_url
            }
        else:  # stdio
            config["mcpServers"][request.server_name] = {
                "type": "stdio",
                "command": request.command,
                "args": request.args
            }
            
        # Write updated configuration
        success = await OllamaMCPPackage.write_ollama_config(config)
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to write configuration file"
            )
            
        # Return updated list of servers
        return {"servers": config["mcpServers"], "message": f"Server '{request.server_name}' added successfully"}
        
    except HTTPException as http_exc:
        # Re-raise HTTPExceptions directly
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error adding MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding MCP server: {str(e)}")

@router.get("/servers/active", tags=["MCP"])
async def get_active_mcp_servers():
    """Get list of active MCP servers"""
    try:
        # Get list of active servers from database
        active_servers = await db.get_active_mcp_servers()
        return {"active_servers": active_servers}
    except Exception as e:
        app_logger.error(f"Error getting active MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting active MCP servers: {str(e)}")

@router.post("/servers/toggle-active/{server_name}", tags=["MCP"])
async def toggle_mcp_server_active(server_name: str, active: bool):
    """Activate or deactivate an MCP server"""
    try:
        # Update server active status in database
        success = await db.set_mcp_server_active(server_name, active)
        if not success:
            raise HTTPException(status_code=404, detail=f"Server {server_name} not found")
        
        # Get updated list of active servers
        active_servers = await db.get_active_mcp_servers()
        return {"active": active, "server_name": server_name, "active_servers": active_servers}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        app_logger.error(f"Error toggling MCP server active status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error toggling MCP server active status: {str(e)}")

@router.get("/test-tools", tags=["MCP"])
async def test_mcp_tools(session_id: str):
    chatbot = manager.get_chatbot(session_id)
    if not chatbot:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        tools_response = await chatbot.session.list_tools()
        return {"tools": [tool.name for tool in tools_response.tools]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")

@router.get("/servers/running", tags=["MCP"])
async def get_running_mcp_servers():
    """Get list of currently running MCP servers"""
    try:
        active_clients = get_active_mcp_clients()
        running_servers = {}
        
        for server_name, client in active_clients.items():
            # Get basic info about the running server
            running_servers[server_name] = {
                "status": "running",
                "model": client.chatbot.model_name if client.chatbot else "unknown",
                "has_session": client.session is not None
            }
        
        return {"running_servers": running_servers, "count": len(running_servers)}
    except Exception as e:
        app_logger.error(f"Error getting running MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting running MCP servers: {str(e)}")

@router.post("/servers/restart", tags=["MCP"])
async def restart_mcp_servers():
    """Restart all MCP servers"""
    try:
        app_logger.info("Restarting MCP servers...")
        
        # Clean up existing connections
        await cleanup_mcp_servers()
        
        # Start servers again
        started_servers = await startMCPServers()
        
        return {
            "message": "MCP servers restarted",
            "started_servers": list(started_servers.keys()),
            "count": len(started_servers)
        }
    except Exception as e:
        app_logger.error(f"Error restarting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error restarting MCP servers: {str(e)}")

@router.post("/servers/start/{server_name}", tags=["MCP"])
async def start_specific_mcp_server(server_name: str):
    """Start a specific MCP server by name"""
    try:
        # Load configuration to get server details
        config = await OllamaMCPPackage.load_mcp_config()
        if not config or "mcpServers" not in config:
            raise HTTPException(status_code=404, detail="No MCP servers configured")
        
        server_config = config["mcpServers"].get(server_name)
        if not server_config:
            raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found in configuration")
        
        # Check if already running
        active_clients = get_active_mcp_clients()
        if server_name in active_clients:
            return {"message": f"Server '{server_name}' is already running", "status": "already_running"}
        
        # Create and start the server
        client = await OllamaMCPPackage.create_client(model_name="llama3.2")
        server_type = server_config.get("type", "stdio")
        success = False
        
        if server_type == "sse":
            server_url = server_config.get("url")
            if not server_url:
                raise HTTPException(status_code=400, detail="Server URL required for SSE server")
            success = await client.connect_to_sse_server(server_url)
        elif server_type == "stdio":
            command = server_config.get("command")
            args = server_config.get("args", [])
            if not command:
                raise HTTPException(status_code=400, detail="Command required for STDIO server")
            success = await client.connect_to_stdio_server(command, args)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported server type: {server_type}")
        
        if success:
            # Add to active clients (import and update the global dict)
            from app.core.lifecycle import active_mcp_clients
            active_mcp_clients[server_name] = client
            return {"message": f"Server '{server_name}' started successfully", "status": "started"}
        else:
            await client.cleanup()
            raise HTTPException(status_code=500, detail=f"Failed to start server '{server_name}'")
            
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error starting MCP server {server_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting MCP server: {str(e)}")
        