from typing import List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str
    
class ChatResponse(BaseModel):
    response: str
    session_id: str

class InitializeRequest(BaseModel):
    model_name: str = "llama3.2"
    system_message: Optional[str] = None
    session_id: Optional[str] = None
    
class InitializeResponse(BaseModel):
    session_id: str
    status: str
    model: str


class StatusResponse(BaseModel):
    status: str
    active_sessions: List[str]
    message: Optional[str] = None

class ChatHistoryItem(BaseModel):
    role: str
    message: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[ChatHistoryItem]
    count: int

class ChatSession(BaseModel):
    session_id: str
    model_name: str
    session_type: str
    system_message: Optional[str] = None
    created_at: str
    last_active: str
    is_active: bool
    message_count: Optional[int] = 0
    first_message_time: Optional[str] = None
    last_message_time: Optional[str] = None

class AvailableChatsResponse(BaseModel):
    sessions: List[ChatSession]
    count: int
