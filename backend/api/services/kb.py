import json
import os
from pathlib import Path
import tempfile
from typing import List, Optional, Dict, Any
import uuid
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
from src.db.aws import S3Client, get_aws_s3_client
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
        self.settings = settings
        self.s3_client = get_aws_s3_client()
        
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
            self.s3_client.create_bucket(f"kb-{kb.id}-{''.join(kb.name.split(' '))}")
            
            self.qdrant_client.create_collection(f"kb-{kb.id}", vector_size=768)
            return kb
        except HTTPException as e:
            session.rollback()
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
        """Create a new document and store it in S3"""
        kb = await self.get_knowledge_base(session, kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        
        temp_file = None
        try:
            # Create temp directory if it doesn't exist
            temp_dir = Path(tempfile.gettempdir()) / "uploads"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            original_filename = Path(filename)
            extension = original_filename.suffix.lower()
            
            # Create temp file with unique name
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
                dir=temp_dir
            )
            
            # Write content to temp file
            with open(temp_file.name, 'wb') as f:
                f.write(file_content)
            
            # Generate S3 path
            date_path = datetime.now().strftime("%Y/%m/%d")
            file_name = f"{uuid.uuid4()}_{filename}"
            bucket_name = f"kb-{kb.id}-{''.join(kb.name.split(' '))}"

            # Upload to S3
            try:
                file_path_in_s3 = self.s3_client.upload_file(
                    bucket_name=bucket_name,
                    object_name=os.path.join(date_path, file_name),
                    file_path=str(temp_file.name),
                )
            except Exception as e:
                logger.error(f"S3 upload failed: {str(e)}")
                raise HTTPException(500, "Failed to upload file to storage")

            # Create document record
            document = Document(
                knowledge_base_id=kb_id,
                name=file_name,
                source=file_path_in_s3,
                extension=extension,
                status=DocumentStatus.UPLOADED,
                extra_info=doc_data.extra_info,
            )
            
            session.add(document)
            session.commit()
            session.refresh(document)
            
            return document
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating document: {str(e)}")
            raise HTTPException(500, f"Failed to create document: {str(e)}")
            
        finally:
            # Cleanup temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {str(e)}")

    async def process_document(
        self,
        kb_id: int,
        doc_id: int,
        session: Session,
    ) -> DocumentResponse:
        """Process document content and create embeddings"""
        # Get knowledge base and document
        kb = session.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
            
        doc = session.query(Document).filter(
            Document.id == doc_id,
            Document.knowledge_base_id == kb_id
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Get RAG config
        rag_config :RAGConfig = kb.rag_config
        if not rag_config:
            raise HTTPException(status_code=404, detail="RAG Config not found")
        
        # Update document status
        doc.status = DocumentStatus.PENDING
        session.commit()
        
        temp_file = None
        try:
            # Create temp directory
            temp_dir = Path(tempfile.gettempdir()) / "downloads"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Create temp file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=doc.extension,
                dir=temp_dir
            )
            
            # Update status to processing
            doc.status = DocumentStatus.PROCESSING
            session.commit()
            
            # Download file from S3
            try:
                self.s3_client.download_file(
                    file_url=doc.source,
                    file_path_to_save=temp_file.name
                )
            except Exception as e:
                logger.error(f"S3 download failed: {str(e)}")
                raise HTTPException(500, "Failed to download file from storage")
            
            # Initialize RAG manager
            rag_manager = RAGManager.create_rag(
                rag_type=rag_config.rag_type,
                qdrant_url=self.settings.QDRANT_URL,
                gemini_api_key=self.settings.GEMINI_CONFIG.api_key,
                chunk_size=rag_config.chunk_size,
                chunk_overlap=rag_config.chunk_overlap,
            )
            
            # Extract and process text
            extractor = self.file_extractor.get_extractor_for_file(temp_file.name)
            if not extractor:
                raise HTTPException(400, f"No extractor found for file type: {doc.extension}")
                
            documents = parse_multiple_files(temp_file.name, extractor)
            
            # Process documents and create chunks
            for document in documents:
                chunks = rag_manager.process_document(
                    document=document.text,
                    document_id=doc.id,
                    collection_name=f"kb-{kb.id}",
                    metadata={
                        **document.metadata,
                        "document_name": doc.name,
                        "created_at": doc.created_at.isoformat(),
                    }
                )
                
                # Create chunks in database
                for chunk_idx, chunk_data in enumerate(chunks):
                    chunk = DocumentChunk(
                        document_id=doc.id,
                        content=chunk_data.text,
                        chunk_index=chunk_idx,
                        embedding=json.dumps(chunk_data.metadata["embedding"]),
                        extra_info=chunk_data.metadata,
                    )
                    session.add(chunk)
            
            # Update document status
            doc.status = DocumentStatus.PROCESSED
            session.commit()
            session.refresh(doc)
            
            return doc
            
        except Exception as e:
            # Update document status to failed
            doc.status = DocumentStatus.FAILED
            session.commit()
            
            logger.error(f"Error processing document: {str(e)}")
            raise HTTPException(500, f"Failed to process document: {str(e)}")
            
        finally:
            # Cleanup temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {str(e)}")
        

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
                collection_name=f"kb-{kb_id}",
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
                collection_name=f"kb-{kb_id}",
                document_id=str(document_id)
            )
            
            # Delete from database
            session.delete(document)  # This will cascade delete chunks
            session.commit()
            
            return {"status": "success", "message": "Document deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise