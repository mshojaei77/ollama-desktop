"""
Enhanced MCP Agent Routes

FastAPI routes for managing MCP agents with latest features including
categories, server templates, and improved error handling.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
import json

try:
    # Try relative imports first (when imported as module)
    from .models import (
        MCPAgent, CreateMCPAgentRequest, UpdateMCPAgentRequest, 
        ChatRequest, ChatResponse, MCPAgentListResponse,
        MCPServerTemplate
    )
    from .service import MCPAgentService
except ImportError:
    # Fall back to absolute imports (when run directly)
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from api.mcp_agents.models import (
        MCPAgent, CreateMCPAgentRequest, UpdateMCPAgentRequest, 
        ChatRequest, ChatResponse, MCPAgentListResponse,
        MCPServerTemplate
    )
    from api.mcp_agents.service import MCPAgentService

from api.logger import app_logger

router = APIRouter(prefix="/mcp-agents", tags=["MCP Agents"])

# Initialize the enhanced service
mcp_service = MCPAgentService()

@router.get("/", response_model=MCPAgentListResponse)
async def get_mcp_agents(
    category: Optional[str] = Query(None, description="Filter by category"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    search: Optional[str] = Query(None, description="Search in name and description")
):
    """Get all MCP agents with optional filtering and enhanced response data"""
    try:
        agents = await mcp_service.get_all_agents()
        
        # Apply filters
        if category:
            agents = [agent for agent in agents if agent.category == category]
        
        if tag:
            agents = [agent for agent in agents if tag in agent.tags]
        
        if search:
            search_lower = search.lower()
            agents = [
                agent for agent in agents 
                if search_lower in agent.name.lower() or search_lower in agent.description.lower()
            ]
        
        # Get additional metadata
        categories = await mcp_service.get_agent_categories()
        total_servers = sum(len(agent.mcp_servers) for agent in agents)
        
        return MCPAgentListResponse(
            agents=agents,
            count=len(agents),
            categories=categories,
            total_servers=total_servers
        )
    except Exception as e:
        app_logger.error(f"Error getting MCP agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP agents: {str(e)}")

@router.get("/categories")
async def get_agent_categories():
    """Get all available agent categories"""
    try:
        categories = await mcp_service.get_agent_categories()
        return {"categories": categories}
    except Exception as e:
        app_logger.error(f"Error getting agent categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

@router.get("/server-templates")
async def get_mcp_server_templates():
    """Get predefined MCP server templates for easy agent configuration"""
    try:
        templates = await mcp_service.get_mcp_server_templates()
        return {"templates": templates}
    except Exception as e:
        app_logger.error(f"Error getting MCP server templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting server templates: {str(e)}")

@router.get("/{agent_id}", response_model=MCPAgent)
async def get_mcp_agent(agent_id: str):
    """Get a specific MCP agent by ID with enhanced data"""
    try:
        agent = await mcp_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP agent: {str(e)}")

@router.post("/", response_model=MCPAgent)
async def create_mcp_agent(request: CreateMCPAgentRequest):
    """Create a new MCP agent with enhanced validation and features"""
    try:
        # Validate MCP server configurations
        for server in request.mcp_servers:
            if server.transport == "stdio" and not server.command:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Command is required for stdio transport (server: {server.name})"
                )
            elif server.transport in ["sse", "streamable-http"] and not server.url:
                raise HTTPException(
                    status_code=400,
                    detail=f"URL is required for {server.transport} transport (server: {server.name})"
                )
        
        agent = await mcp_service.create_agent(request)
        app_logger.info(f"Created MCP agent: {agent.id} ({agent.name})")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error creating MCP agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating MCP agent: {str(e)}")

@router.put("/{agent_id}", response_model=MCPAgent)
async def update_mcp_agent(agent_id: str, request: UpdateMCPAgentRequest):
    """Update an MCP agent with enhanced validation"""
    try:
        # Convert request to dict, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Validate MCP server configurations if provided
        if 'mcp_servers' in updates:
            for server in updates['mcp_servers']:
                if isinstance(server, dict):
                    transport = server.get('transport', 'stdio')
                    if transport == "stdio" and not server.get('command'):
                        raise HTTPException(
                            status_code=400,
                            detail=f"Command is required for stdio transport (server: {server.get('name', 'unknown')})"
                        )
                    elif transport in ["sse", "streamable-http"] and not server.get('url'):
                        raise HTTPException(
                            status_code=400,
                            detail=f"URL is required for {transport} transport (server: {server.get('name', 'unknown')})"
                        )
        
        agent = await mcp_service.update_agent(agent_id, updates)
        if not agent:
            raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
        
        app_logger.info(f"Updated MCP agent: {agent_id} ({agent.name})")
        return agent
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error updating MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating MCP agent: {str(e)}")

@router.delete("/{agent_id}")
async def delete_mcp_agent(agent_id: str, background_tasks: BackgroundTasks):
    """Delete an MCP agent (soft delete)"""
    try:
        deleted = await mcp_service.delete_agent(agent_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
        
        app_logger.info(f"Deleted MCP agent: {agent_id}")
        return {"status": "success", "message": f"MCP agent {agent_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error deleting MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting MCP agent: {str(e)}")

@router.delete("/{agent_id}/permanent")
async def delete_mcp_agent_permanently(agent_id: str, background_tasks: BackgroundTasks):
    """Permanently delete an MCP agent from the database"""
    try:
        deleted = await mcp_service.delete_agent_permanently(agent_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
        
        app_logger.info(f"Permanently deleted MCP agent: {agent_id}")
        return {"status": "success", "message": f"MCP agent {agent_id} permanently deleted"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error permanently deleting MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error permanently deleting MCP agent: {str(e)}")

@router.post("/{agent_id}/start")
async def start_mcp_agent(agent_id: str):
    """Start an MCP agent with enhanced error reporting"""
    try:
        agent = await mcp_service.start_agent(agent_id)
        if not agent:
            agent_config = await mcp_service.get_agent(agent_id)
            if not agent_config:
                raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
            else:
                # Check for common configuration issues
                error_details = []
                for server in agent_config.mcp_servers:
                    if not server.enabled:
                        continue
                    if server.transport == "stdio" and not server.command:
                        error_details.append(f"Server '{server.name}' has no command configured")
                    elif server.transport in ["sse", "streamable-http"] and not server.url:
                        error_details.append(f"Server '{server.name}' has no URL configured")
                    if server.env:
                        for env_var, value in server.env.items():
                            if not value and env_var:  # Empty environment variable
                                error_details.append(f"Server '{server.name}' requires environment variable '{env_var}'")
                
                if error_details:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Agent configuration issues: {'; '.join(error_details)}"
                    )
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to start agent - check server logs for details"
                    )
        
        app_logger.info(f"Started MCP agent: {agent_id}")
        return {"status": "success", "message": f"MCP agent {agent_id} started successfully"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error starting MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error starting MCP agent: {str(e)}")

@router.post("/{agent_id}/chat", response_model=ChatResponse)
async def chat_with_mcp_agent(agent_id: str, request: ChatRequest):
    """Send a message to an MCP agent with enhanced error handling"""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        response = await mcp_service.chat_with_agent(agent_id, request.message)
        
        # Check if response indicates an error
        if response.startswith("Error:"):
            if "not found" in response.lower():
                raise HTTPException(status_code=404, detail="Agent not found or could not be started")
            elif "configuration" in response.lower():
                raise HTTPException(status_code=400, detail=response)
            else:
                raise HTTPException(status_code=500, detail=response)
        
        return ChatResponse(
            response=response, 
            agent_id=agent_id,
            session_id=request.session_id
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error chatting with MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error chatting with MCP agent: {str(e)}")

@router.post("/{agent_id}/chat/stream")
async def stream_chat_with_mcp_agent(agent_id: str, request: ChatRequest):
    """Stream chat with an MCP agent with enhanced error handling"""
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        return StreamingResponse(
            mcp_service.stream_chat_with_agent(agent_id, request.message),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error streaming with MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error streaming with MCP agent: {str(e)}")

@router.get("/models/available")
async def get_available_models():
    """Get available Ollama models for MCP agents"""
    try:
        models = await mcp_service.get_available_models()
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")

@router.post("/cleanup")
async def cleanup_all_mcp_agents():
    """Clean up all active MCP agents"""
    try:
        await mcp_service.cleanup_all_agents()
        app_logger.info("Cleaned up all MCP agents")
        return {"status": "success", "message": "All MCP agents cleaned up successfully"}
    except Exception as e:
        app_logger.error(f"Error cleaning up MCP agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cleaning up MCP agents: {str(e)}")

@router.get("/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Get the status of an MCP agent (active/inactive)"""
    try:
        agent_config = await mcp_service.get_agent(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
        
        is_active = agent_id in mcp_service.active_agents
        active_servers = 0
        server_status = []
        
        if is_active:
            for server in agent_config.mcp_servers:
                if server.enabled:
                    active_servers += 1
                    server_status.append({
                        "name": server.name,
                        "transport": server.transport,
                        "enabled": server.enabled,
                        "description": server.description
                    })
        
        return {
            "agent_id": agent_id,
            "is_active": is_active,
            "total_servers": len(agent_config.mcp_servers),
            "active_servers": active_servers,
            "server_status": server_status,
            "model": f"{agent_config.model_provider}/{agent_config.model_name}",
            "category": agent_config.category,
            "version": agent_config.version
        }
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error getting agent status {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting agent status: {str(e)}")

@router.post("/{agent_id}/stop")
async def stop_mcp_agent(agent_id: str):
    """Stop an active MCP agent"""
    try:
        if agent_id not in mcp_service.active_agents:
            raise HTTPException(status_code=400, detail=f"MCP agent {agent_id} is not currently active")
        
        await mcp_service._cleanup_agent(agent_id)
        app_logger.info(f"Stopped MCP agent: {agent_id}")
        return {"status": "success", "message": f"MCP agent {agent_id} stopped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error stopping MCP agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error stopping MCP agent: {str(e)}")

@router.get("/{agent_id}/validate")
async def validate_agent_config(agent_id: str):
    """Validate an MCP agent's configuration"""
    try:
        agent_config = await mcp_service.get_agent(agent_id)
        if not agent_config:
            raise HTTPException(status_code=404, detail=f"MCP agent {agent_id} not found")
        
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "server_validations": []
        }
        
        # Validate agent configuration
        if not agent_config.instructions:
            validation_results["warnings"].append("No instructions provided for the agent")
        
        if not agent_config.mcp_servers:
            validation_results["warnings"].append("No MCP servers configured")
        
        # Validate each MCP server
        for server in agent_config.mcp_servers:
            server_validation = {
                "name": server.name,
                "transport": server.transport,
                "valid": True,
                "errors": [],
                "warnings": []
            }
            
            if server.transport == "stdio":
                if not server.command:
                    server_validation["errors"].append("Command is required for stdio transport")
                    server_validation["valid"] = False
            elif server.transport in ["sse", "streamable-http"]:
                if not server.url:
                    server_validation["errors"].append(f"URL is required for {server.transport} transport")
                    server_validation["valid"] = False
            
            # Check for missing environment variables
            if server.env:
                for env_var, value in server.env.items():
                    if not value and env_var:
                        server_validation["warnings"].append(f"Environment variable '{env_var}' is not set")
            
            validation_results["server_validations"].append(server_validation)
            
            if not server_validation["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(server_validation["errors"])
            
            validation_results["warnings"].extend(server_validation["warnings"])
        
        return validation_results
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error validating agent config {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error validating agent config: {str(e)}")

@router.post("/initialize-prebuilt")
async def initialize_prebuilt_agents():
    """Initialize pre-built MCP agents for new users"""
    try:
        created = await mcp_service.initialize_prebuilt_agents_if_empty()
        if created:
            app_logger.info("Pre-built MCP agents initialized")
            return {
                "status": "success", 
                "message": "Pre-built agents created successfully",
                "prebuilt_created": True
            }
        else:
            return {
                "status": "success", 
                "message": "Pre-built agents already exist or were not needed",
                "prebuilt_created": False
            }
    except Exception as e:
        app_logger.error(f"Error initializing pre-built agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing pre-built agents: {str(e)}")

@router.post("/create-prebuilt")
async def create_prebuilt_agents():
    """Force create pre-built MCP agents"""
    try:
        prebuilt_agents = await mcp_service.create_prebuilt_agents()
        app_logger.info(f"Created {len(prebuilt_agents)} pre-built MCP agents")
        return {
            "status": "success", 
            "message": f"Created {len(prebuilt_agents)} pre-built agents",
            "agents": prebuilt_agents
        }
    except Exception as e:
        app_logger.error(f"Error creating pre-built agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating pre-built agents: {str(e)}")

@router.get("/prebuilt")
async def get_prebuilt_agents():
    """Get all pre-built MCP agents"""
    try:
        agents = await mcp_service.get_prebuilt_agents()
        return {
            "agents": agents,
            "count": len(agents)
        }
    except Exception as e:
        app_logger.error(f"Error getting pre-built agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting pre-built agents: {str(e)}")

@router.get("/user-created")
async def get_user_created_agents():
    """Get all user-created MCP agents"""
    try:
        agents = await mcp_service.get_user_created_agents()
        return {
            "agents": agents,
            "count": len(agents)
        }
    except Exception as e:
        app_logger.error(f"Error getting user-created agents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting user-created agents: {str(e)}") 