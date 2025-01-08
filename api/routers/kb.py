from fastapi import  APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.readers.docling import DoclingReader
from src.db.rag_manager import RAGManager
from config import Settings

kb_router = APIRouter(prefix="/kb", tags=["kb"])
# Initialize components
settings = Settings()
reader = DoclingReader(
    num_threads=4,
    enable_ocr=True,
    enable_tables=True
)
rag_manager = RAGManager(
    qdrant_url=settings.QDRANT_URL,
    gemini_api_key=settings.GEMINI_API_KEY,
    chunk_size=512,
    chunk_overlap=64
)

class QueryRequest(BaseModel):
    query: str
    collection_name: str
    limit: Optional[int] = 5

@kb_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_name: str = "documents"
):
    """Upload and process a document"""
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    try:
        # Read file content
        content = await file.read()
        
        # Process with DoclingReader
        doc_result = reader.process_bytes(
            file_bytes=content,
            file_extension='.pdf'
        )
        
        # Process with RAG Manager
        document_id = rag_manager.process_document(
            document=doc_result["markdown_content"],
            collection_name=collection_name,
            metadata={
                "filename": file.filename,
                "num_pages": doc_result["metadata"]["num_pages"]
            }
        )
        
        return {
            "status": "success",
            "document_id": document_id,
            "pages": len(doc_result["pages"]),
            "collection": collection_name
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))

@kb_router.post("/query")
async def query_documents(request: QueryRequest):
    """Query processed documents"""
    try:
        response = rag_manager.search(
            query=request.query,
            collection_name=request.collection_name,
            limit=request.limit
        )
        return {"response": response}
        
    except Exception as e:
        raise HTTPException(500, str(e))

@kb_router.delete("/document/{collection_name}/{document_id}")
async def delete_document(collection_name: str, document_id: str):
    """Delete a document"""
    try:
        rag_manager.delete_document(
            collection_name=collection_name,
            document_id=document_id
        )
        return {"status": "success"}
        
    except Exception as e:
        raise HTTPException(500, str(e))


    