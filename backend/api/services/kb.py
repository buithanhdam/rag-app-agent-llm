from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from api.schemas.kb import (
    KnowledgeBaseCreate, 
    KnowledgeBaseResponse, 
    KnowledgeBaseUpdate,
    DocumentCreate,
    DocumentResponse
)
from src.db.models import (
    KnowledgeBase,
    RAGConfig,
    Document,
    DocumentStatus,
    DocumentChunk
)
from src.db.qdrant import QdrantVectorDatabase
from src.readers import parse_multiple_files, FileExtractor
from src.rag.rag_manager import RAGManager
from src.config import Settings
from src.logger import get_formatted_logger

logger = get_formatted_logger(__file__)

class KnowledgeBaseService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.file_extractor = FileExtractor()
        self.qdrant_client = QdrantVectorDatabase(url=settings.QDRANT_URL)
        # self.rag_manager = RAGManager.create_rag(
        #     rag_type=settings.RAG_CONFIG.rag_type,
        #     qdrant_url=settings.QDRANT_URL,
        #     gemini_api_key=settings.GEMINI_CONFIG.api_key,
        #     chunk_size=settings.RAG_CONFIG.chunk_size,
        #     chunk_overlap=settings.RAG_CONFIG.chunk_overlap,
        # )
        
    async def create_knowledge_base(
        self, 
        session: Session, 
        kb_data: KnowledgeBaseCreate
    ) -> KnowledgeBaseResponse:
        """Create a new knowledge base with RAG configuration"""
        
        # First create the RAG config
        try:
            rag_config = RAGConfig(
                rag_type=kb_data.rag_type,
                embedding_model=kb_data.embedding_model,
                similarity_type=kb_data.similarity_type,
                chunk_size=kb_data.chunk_size,
                chunk_overlap=kb_data.chunk_overlap,
                configuration={},  # Add any additional config here
                is_active=True
            )
            session.add(rag_config)
            session.flush()  # Get the rag_config.id
            
            # Create the knowledge base
            kb = KnowledgeBase(
                name=kb_data.name,
                description=kb_data.description,
                rag_config_id=rag_config.id,
                extra_info=kb_data.extra_info,
                is_active=True
            )
            session.add(kb)
            session.commit()
            session.refresh(kb)
            
            self.qdrant_client.create_collection(f"kb_{kb.id}", vector_size=768)
            
            return kb
        except HTTPException as e:
            raise e

    async def update_knowledge_base(
        self,
        session: Session,
        kb_id: int,
        kb_data: KnowledgeBaseUpdate
    ) -> KnowledgeBaseResponse:
        """Update an existing knowledge base"""
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        update_data = kb_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(kb, key, value)
        
        kb.updated_at = datetime.utcnow()
        session.commit()
        session.refresh(kb)
        return kb

    async def list_knowledge_bases(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 10
    ) -> List[KnowledgeBaseResponse]:
        """List all knowledge bases"""
        return session.query(KnowledgeBase)\
            .offset(skip)\
            .limit(limit)\
            .all()

    async def get_knowledge_base(
        self,
        session: Session,
        kb_id: int
    ) -> KnowledgeBaseResponse:
        """Get a specific knowledge base"""
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return kb

    async def get_documents_by_kb( self,
        session: Session,
        kb_id: int)-> List[DocumentResponse]:
        return session.query(Document).filter(Document.knowledge_base_id == kb_id).all()

    async def create_document(
        self,
        session: Session,
        kb_id: int,
        doc_data: DocumentCreate,
        file_content: bytes,
        filename: str
    ) -> DocumentResponse:
        """Create a new document and process it"""
        # Verify knowledge base exists
        kb = await self.get_knowledge_base(session, kb_id)
        
        # Create document record
        document = Document(
            knowledge_base_id=kb_id,
            title=doc_data.title,
            source=doc_data.source or filename,
            content_type=doc_data.content_type,
            status=DocumentStatus.PROCESSING,
            extra_info=doc_data.extra_info
        )
        session.add(document)
        session.flush()  # Get document.id
        
        try:
            # Process the document content
            processed_data = await self.process_document(
                file_content=file_content,
                filename=filename,
                collection_name=f"kb_{kb_id}",
                metadata={"document_id": document.id, **doc_data.extra_info} if doc_data.extra_info else {"document_id": document.id}
            )
            
            # Create document chunks
            for chunk_idx, chunk_data in enumerate(processed_data["chunks"]):
                chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_data["text"],
                    chunk_index=chunk_idx,
                    embedding=chunk_data["embedding"],
                    extra_info=chunk_data.get("metadata", {})
                )
                session.add(chunk)
            
            # Update document status
            document.status = DocumentStatus.PROCESSED
            document.processed_content = processed_data.get("processed_content")
            
        except Exception as e:
            document.status = DocumentStatus.FAILED
            logger.error(f"Error processing document: {str(e)}")
            raise
        
        finally:
            session.commit()
            session.refresh(document)
            
        return document

    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        collection_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process document content and create embeddings"""
        try:
            # Extract text content
            documents = parse_multiple_files(
                file_content,
                extractor=self.file_extractor.get_extractor_for_file(filename)
            )
            
            # Process with RAG Manager
            processed_results = []
            for doc in documents:
                result = self.rag_manager.process_document(
                    document=doc.text,
                    collection_name=collection_name,
                    metadata=metadata
                )
                processed_results.append(result)
            
            return {
                "status": "success",
                "processed_content": "\n".join([doc.text for doc in documents]),
                "chunks": processed_results,
                "total": len(processed_results),
                "collection": collection_name
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    async def query_documents(
        self,
        session: Session,
        kb_id: int,
        query: str,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Query documents within a specific knowledge base"""
        kb = await self.get_knowledge_base(session, kb_id)
        
        try:
            response = self.rag_manager.search(
                query=query,
                collection_name=f"kb_{kb_id}",
                limit=limit
            )
            return {
                "knowledge_base": kb.name,
                "query": query,
                "response": response
            }
            
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            raise

    async def delete_document(
        self,
        session: Session,
        kb_id: int,
        document_id: int
    ) -> Dict[str, str]:
        """Delete a document and its chunks"""
        document = session.query(Document)\
            .filter(Document.id == document_id, Document.knowledge_base_id == kb_id)\
            .first()
            
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        try:
            # Delete from vector store
            self.rag_manager.delete_document(
                collection_name=f"kb_{kb_id}",
                document_id=str(document_id)
            )
            
            # Delete from database
            session.delete(document)  # This will cascade delete chunks
            session.commit()
            
            return {"status": "success", "message": "Document deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise