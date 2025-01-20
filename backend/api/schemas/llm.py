# src/schemas/llm.py
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class LLMProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini" 
    ANTHROPIC = "anthropic"

class LLMFoundationCreate(BaseModel):
    provider: LLMProvider
    model_name: str
    model_id: str
    description: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None

class LLMFoundationUpdate(BaseModel):
    provider: Optional[LLMProvider] = None
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class LLMFoundationResponse(BaseModel):
    id: int
    provider: LLMProvider
    model_name: str
    model_id: str
    description: Optional[str]
    capabilities: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

class LLMConfigCreate(BaseModel):
    foundation_id: int
    name: str
    temperature: float
    max_tokens: int
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    system_prompt: str
    stop_sequences: Optional[List[str]] = None

class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    system_prompt: Optional[str] = None
    stop_sequences: Optional[List[str]] = None

class LLMConfigResponse(BaseModel):
    id: int
    foundation_id: int
    name: str
    temperature: float
    max_tokens: int
    top_p: Optional[float]
    frequency_penalty: Optional[float]
    presence_penalty: Optional[float]
    system_prompt: str
    stop_sequences: Optional[List[str]]
    created_at: datetime
    updated_at: Optional[datetime]