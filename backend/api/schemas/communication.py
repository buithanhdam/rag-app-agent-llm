from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from .agent import AgentResponse

class AgentCommunicationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    agent_ids: List[int]  # List of agent IDs to include in communication

class AgentCommunicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AgentCommunicationMemberCreate(BaseModel):
    communication_id: int
    agent_id: int
    role: Optional[str] = "member"

class AgentCommunicationResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    configuration: Optional[Dict[str, Any]]
    agents: List[AgentResponse]  # Reuse existing AgentResponse

class CommunicationMessageCreate(BaseModel):
    conversation_id: int
    role: str
    content: str
    communication_id: int  # Added to identify the communication context