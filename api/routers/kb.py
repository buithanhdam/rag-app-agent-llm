# src/routers/kb_router.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config import Settings
from api.services.kb import KnowledgeBaseService

kb_router = APIRouter(prefix="/kb", tags=["kb"])

class QueryRequest(BaseModel):
    query: str
    collection_name: str
    limit: Optional[int] = 5

# Dependency to get KB service
async def get_kb_service():
    settings = Settings()
    return KnowledgeBaseService(settings)

@kb_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "documents",
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Upload and process a document"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    try:
        content = await file.read()
        return await kb_service.process_document(
            file_content=content,
            filename=file.filename,
            collection_name=collection_name
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))

@kb_router.post("/query")
async def query_documents(
    request: QueryRequest,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Query processed documents"""
    try:
        return await kb_service.query_documents(
            query=request.query,
            collection_name=request.collection_name,
            limit=request.limit
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))

@kb_router.delete("/document/{collection_name}/{document_id}")
async def delete_document(
    collection_name: str,
    document_id: str,
    kb_service: KnowledgeBaseService = Depends(get_kb_service)
):
    """Delete a document"""
    try:
        return await kb_service.delete_document(
            collection_name=collection_name,
            document_id=document_id
        )
        
    except Exception as e:
        raise HTTPException(500, str(e))