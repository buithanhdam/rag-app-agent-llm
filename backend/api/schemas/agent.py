from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from src.db.models import AgentType
class AgentCreate(BaseModel):
    name: str
    foundation_id: Optional[int] = None
    agent_type: AgentType
    config_id: Optional[int] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    agent_type: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AgentResponse(BaseModel):
    id: int
    name: str
    foundation_id: int
    config_id:int
    agent_type: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    configuration: Optional[Dict[str, Any]]
    tools: Optional[List[str]]