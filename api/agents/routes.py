"""
Agent API Routes

This module defines FastAPI routes for interacting with agents.
"""

import json
import logging
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .registry import agent_registry


# Setup logging
logger = logging.getLogger("agent_routes")

# Create a router for agent endpoints
router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
    responses={404: {"description": "Not found"}}
)


# ----- Pydantic Models for Request/Response -----

class AgentMetadata(BaseModel):
    """Agent metadata model."""
    id: str
    name: str
    description: str
    icon: str
    tags: List[str]


class AgentListResponse(BaseModel):
    """Response model for listing agents."""
    agents: List[AgentMetadata]
    count: int


class AgentMessageRequest(BaseModel):
    """Request model for sending a message to an agent."""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentMessageResponse(BaseModel):
    """Response model for an agent message."""
    response: str
    agent_id: str
    session_id: Optional[str] = None


# ----- API Routes -----

@router.get("", response_model=AgentListResponse)
async def list_agents():
    """
    List all available agents.
    
    Returns:
        A list of agent metadata
    """
    # Ensure registry is initialized
    if not agent_registry._initialized:
        await agent_registry.initialize()
    
    agents_metadata = agent_registry.get_all_agents()
    
    return AgentListResponse(
        agents=[AgentMetadata(**metadata) for metadata in agents_metadata],
        count=len(agents_metadata)
    )


@router.get("/{agent_id}", response_model=AgentMetadata)
async def get_agent(agent_id: str):
    """
    Get information about a specific agent.
    
    Args:
        agent_id: The ID of the agent
        
    Returns:
        The agent's metadata
    """
    # Ensure registry is initialized
    if not agent_registry._initialized:
        await agent_registry.initialize()
    
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    
    return AgentMetadata(**agent.get_metadata())


@router.get("/tag/{tag}", response_model=AgentListResponse)
async def get_agents_by_tag(tag: str):
    """
    Get all agents with a specific tag.
    
    Args:
        tag: The tag to filter by
        
    Returns:
        A list of agent metadata
    """
    # Ensure registry is initialized
    if not agent_registry._initialized:
        await agent_registry.initialize()
    
    agents_metadata = agent_registry.get_agents_by_tag(tag)
    
    return AgentListResponse(
        agents=[AgentMetadata(**metadata) for metadata in agents_metadata],
        count=len(agents_metadata)
    )


@router.post("/{agent_id}/message", response_model=AgentMessageResponse)
async def send_message_to_agent(agent_id: str, request: AgentMessageRequest):
    """
    Send a message to an agent and get a response.
    
    Args:
        agent_id: The ID of the agent
        request: The message request
        
    Returns:
        The agent's response
    """
    # Ensure registry is initialized
    if not agent_registry._initialized:
        await agent_registry.initialize()
    
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    
    try:
        response = await agent.process(
            message=request.message,
            session_id=request.session_id,
            context=request.context
        )
        
        return AgentMessageResponse(
            response=response,
            agent_id=agent_id,
            session_id=request.session_id
        )
    except Exception as e:
        logger.error(f"Error processing message with agent {agent_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing message: {str(e)}"
        )


@router.post("/{agent_id}/message/stream")
async def stream_message_to_agent(agent_id: str, request: AgentMessageRequest):
    """
    Send a message to an agent and stream the response.
    
    Args:
        agent_id: The ID of the agent
        request: The message request
        
    Returns:
        A streaming response of the agent's reply
    """
    # Ensure registry is initialized
    if not agent_registry._initialized:
        await agent_registry.initialize()
    
    agent = agent_registry.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    
    async def generate_stream():
        try:
            async for chunk in agent.process_stream(
                message=request.message,
                session_id=request.session_id,
                context=request.context
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            
            # Signal completion
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"Error streaming message with agent {agent_id}: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    ) 