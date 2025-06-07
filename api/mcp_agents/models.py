"""
MCP Agent Models

Pydantic models for MCP agent configuration and responses.
Updated to support latest Agno MCP features including multiple transport types.
"""

from typing import Dict, List, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server with support for multiple transport types."""
    name: str = Field(..., description="Unique name for this MCP server")
    transport: Literal["stdio", "sse", "streamable-http"] = Field(default="stdio", description="Transport type")
    
    # For stdio transport
    command: Optional[str] = Field(None, description="Command to run the MCP server (for stdio)")
    args: Optional[List[str]] = Field(default_factory=list, description="Arguments for the command")
    
    # For SSE/HTTP transports
    url: Optional[str] = Field(None, description="URL for the MCP server (for sse/streamable-http)")
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="HTTP headers")
    timeout: Optional[int] = Field(default=30, description="Connection timeout in seconds")
    sse_read_timeout: Optional[int] = Field(default=60, description="SSE read timeout in seconds")
    
    # Environment variables
    env: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")
    
    # Additional settings
    enabled: bool = Field(default=True, description="Whether this server is enabled")
    description: Optional[str] = Field(None, description="Description of what this server provides")

    @validator('command', 'url')
    def validate_transport_config(cls, v, values):
        """Validate that the correct configuration is provided for each transport type."""
        transport = values.get('transport', 'stdio')
        if transport == 'stdio' and not values.get('command') and not v:
            raise ValueError("Command is required for stdio transport")
        elif transport in ['sse', 'streamable-http'] and not values.get('url') and not v:
            raise ValueError("URL is required for SSE and streamable-http transports")
        return v


class MCPAgentConfig(BaseModel):
    """Configuration for an MCP agent with enhanced features."""
    id: str = Field(..., description="Unique identifier for the agent")
    name: str = Field(..., description="Display name of the agent")
    description: str = Field(..., description="Description of what the agent does")
    instructions: List[str] = Field(..., description="System instructions for the agent")
    
    # Model configuration
    model_name: str = Field(default="llama3.2", description="Model to use for the agent")
    model_provider: str = Field(default="ollama", description="Model provider")
    
    # MCP configuration
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list, description="MCP servers to connect to")
    
    # Categorization and metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    category: Optional[str] = Field(None, description="Category (e.g., 'development', 'research', 'productivity')")
    icon: Optional[str] = Field(None, description="Icon URL or emoji")
    
    # User interaction
    example_prompts: List[str] = Field(default_factory=list, description="Example prompts for the UI")
    welcome_message: Optional[str] = Field(None, description="Welcome message shown to users")
    
    # Agent behavior
    markdown: bool = Field(default=True, description="Whether to use markdown formatting")
    show_tool_calls: bool = Field(default=True, description="Whether to show tool calls to users")
    add_datetime_to_instructions: bool = Field(default=False, description="Add current datetime to instructions")
    
    # Timestamps
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    # Version and status
    version: str = Field(default="1.0.0", description="Agent version")
    is_active: bool = Field(default=True, description="Whether the agent is active")


class MCPAgent(BaseModel):
    """MCP Agent model for API responses."""
    id: str
    name: str
    description: str
    instructions: List[str]
    model_name: str
    model_provider: str = "ollama"
    mcp_servers: List[MCPServerConfig]
    tags: List[str] = []
    category: Optional[str] = None
    icon: str = ""
    example_prompts: List[str] = []
    welcome_message: Optional[str] = None
    markdown: bool = True
    show_tool_calls: bool = True
    add_datetime_to_instructions: bool = False
    version: str = "1.0.0"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MCPAgentListResponse(BaseModel):
    """Response model for listing MCP agents."""
    agents: List[MCPAgent]
    count: int
    categories: List[str] = []
    total_servers: int = 0


class CreateMCPAgentRequest(BaseModel):
    """Request model for creating an MCP agent."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field("", max_length=500)
    instructions: List[str] = Field(default=["You are a helpful AI assistant."], min_items=1)
    model_name: str = Field(default="llama3.2")
    model_provider: str = Field(default="ollama")
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    category: Optional[str] = None
    icon: Optional[str] = ""
    example_prompts: Optional[List[str]] = Field(default_factory=list)
    welcome_message: Optional[str] = None
    markdown: bool = True
    show_tool_calls: bool = True
    add_datetime_to_instructions: bool = False


class UpdateMCPAgentRequest(BaseModel):
    """Request model for updating an MCP agent."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    instructions: Optional[List[str]] = None
    model_name: Optional[str] = None
    model_provider: Optional[str] = None
    mcp_servers: Optional[List[MCPServerConfig]] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    icon: Optional[str] = None
    example_prompts: Optional[List[str]] = None
    welcome_message: Optional[str] = None
    markdown: Optional[bool] = None
    show_tool_calls: Optional[bool] = None
    add_datetime_to_instructions: Optional[bool] = None
    is_active: Optional[bool] = None


class MCPAgentMessageRequest(BaseModel):
    """Request model for sending a message to an MCP agent."""
    message: str = Field(..., description="The message to send to the agent")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")
    stream: bool = Field(default=True, description="Whether to stream the response")


class MCPAgentMessageResponse(BaseModel):
    """Response model for MCP agent messages."""
    response: str
    agent_id: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    response: str
    agent_id: str
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MCPServerTemplate(BaseModel):
    """Template for commonly used MCP servers."""
    name: str
    description: str
    transport: str
    command: Optional[str] = None
    url: Optional[str] = None
    env_vars: List[str] = []  # List of required environment variables
    category: str
    tags: List[str] = []
    example_instructions: List[str] = []
    icon: Optional[str] = None


class AgentTemplate(BaseModel):
    """Template for creating agents with pre-configured MCP servers."""
    name: str
    description: str
    category: str
    instructions: List[str]
    mcp_servers: List[MCPServerConfig]
    tags: List[str]
    example_prompts: List[str]
    icon: Optional[str] = None
    welcome_message: Optional[str] = None 