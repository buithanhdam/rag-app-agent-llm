from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from src.db.models import DocumentStatus, RAGType
class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None
    rag_type: RAGType
    embedding_model: str
    similarity_type: str
    chunk_size: int = Field(ge=1)
    chunk_overlap: int = Field(ge=0)

class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    extra_info: Optional[Dict[str, Any]] = None

class KnowledgeBaseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    extra_info: Optional[Dict[str, Any]]
    
class DocumentCreate(BaseModel):
    knowledge_base_id: int
    title: str
    source: Optional[str] = None
    content_type: str
    extra_info: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    id: int
    knowledge_base_id: int
    title: str
    source: Optional[str]
    content_type: str
    status: DocumentStatus
    extra_info: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

class QueryRequest(BaseModel):
    query: str
    collection_name: str
    limit: Optional[int] = 5