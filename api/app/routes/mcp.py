from app.core.chatbot import OllamaMCPPackage, app_logger
from app.database import database as db
from app.schemas.mcp import MCPServerAddRequest
from fastapi import APIRouter, HTTPException
from app.core.chatbot_manager import ChatbotManager

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
        