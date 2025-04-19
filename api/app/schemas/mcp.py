from typing import List, Optional
from pydantic import BaseModel

class MCPServerConnectRequest(BaseModel):
    server_type: str  # "sse", "stdio", or "config"
    server_url: Optional[str] = None  # For SSE or server name for config
    command: Optional[str] = None
    args: Optional[List[str]] = None
    session_id: Optional[str] = None
    model_name: str = "llama3.2"

class MCPServerAddRequest(BaseModel):
    server_name: str
    server_type: str = "stdio"  # "sse" or "stdio"
    command: Optional[str] = None  # For STDIO
    args: Optional[List[str]] = None  # For STDIO
    server_url: Optional[str] = None  # For SSE

