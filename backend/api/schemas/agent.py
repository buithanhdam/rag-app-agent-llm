from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class AgentCreate(BaseModel):
    name: str
    agent_type: str
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
    agent_type: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    configuration: Optional[Dict[str, Any]]
    tools: Optional[List[str]]