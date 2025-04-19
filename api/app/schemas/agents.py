from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class AgentMetadata(BaseModel):
    """Agent metadata model."""
    id: str
    name: str
    description: str
    icon: str
    tags: List[str]
    examplePrompts: Optional[List[str]] = None


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

