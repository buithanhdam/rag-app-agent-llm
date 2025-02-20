import json
from typing import List
from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from src.config import Settings
from src.db.mysql import get_db
from api.services.kb import KnowledgeBaseService
from api.schemas.kb import (
    QueryRequest,
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    DocumentCreate,
    DocumentResponse
)

kb_router = APIRouter(prefix="/kb", tags=["kb"])

# Dependency to get KB service
async def get_kb_service():
    settings = Settings()
    return KnowledgeBaseService(settings)

@kb_router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Create a new knowledge base with RAG configuration"""
    return await kb_service.create_knowledge_base(db, kb_data)

@kb_router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Update an existing knowledge base"""
    return await kb_service.update_knowledge_base(db, kb_id, kb_data)

@kb_router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """List all knowledge bases"""
    return await kb_service.list_knowledge_bases(db, skip, limit)

@kb_router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Get a specific knowledge base"""
    return await kb_service.get_knowledge_base(db, kb_id)

@kb_router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def get_documents(
    kb_id: int,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Get a specific knowledge base"""
    return await kb_service.get_documents_by_kb(db, kb_id)


@kb_router.post("/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(
    kb_id: int,
    doc_data: str = Form(...),  # Change to string
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Upload and process a document for a specific knowledge base"""
    # Validate file type if needed
    if not file.filename.lower().endswith(('.pdf', '.txt', '.doc', '.docx')):
        raise HTTPException(400, "Unsupported file type")
        
    try:
        # Parse the JSON string
        doc_data_dict = json.loads(doc_data)
        doc_data_obj = DocumentCreate(**doc_data_dict)
        
        content = await file.read()
        return await kb_service.create_document(
            session=db,
            kb_id=kb_id,
            doc_data=doc_data_obj,
            file_content=content,
            filename=file.filename
        )
            
    except Exception as e:
        raise HTTPException(500, str(e))

@kb_router.post("/{kb_id}/query")
async def query_documents(
    kb_id: int,
    request: QueryRequest,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Query documents within a specific knowledge base"""
    try:
        return await kb_service.query_documents(
            session=db,
            kb_id=kb_id,
            query=request.query,
            limit=request.limit
        )
            
    except Exception as e:
        raise HTTPException(500, str(e))

@kb_router.delete("/{kb_id}/documents/{document_id}")
async def delete_document(
    kb_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Delete a document from a knowledge base"""
    try:
        return await kb_service.delete_document(
            session=db,
            kb_id=kb_id,
            document_id=document_id
        )
            
    except Exception as e:
        raise HTTPException(500, str(e))