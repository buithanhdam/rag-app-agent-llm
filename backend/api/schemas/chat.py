from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.db.models import MessageType
class ConversationCreate(BaseModel):
    title: Optional[str] = None
    agent_id: int
class CommunicationConversationCreate(BaseModel):
    communication_id: int
    title: Optional[str] = None
class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None

class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    messages: List["MessageResponse"]

class MessageCreate(BaseModel):
    conversation_id: int
    role: str
    content: str
    type: MessageType

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

ConversationResponse.update_forward_refs()