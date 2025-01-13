# src/services/kb.py
import os
from pathlib import Path
import tempfile
from typing import Optional, Dict, Any

from fastapi.responses import FileResponse
from src.readers import parse_multiple_files, FileExtractor
from src.db.rag_manager import RAGManager
from config import Settings
from src.logger import get_formatted_logger

logger = get_formatted_logger(__file__)

class KnowledgeBaseService:
    """Service layer for handling document processing and RAG operations"""
    
    def __init__(self, settings: Settings):
        """
        Initialize the KB service with configurations
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        
        # Initialize DoclingReader
        self.file_extractor = FileExtractor()
        # Initialize RAG Manager
        self.rag_manager = RAGManager(
            qdrant_url=settings.QDRANT_URL,
            gemini_api_key=settings.GEMINI_CONFIG.api_key,
            chunk_size=settings.RAG_CONFIG.chunk_size,
            chunk_overlap=settings.RAG_CONFIG.chunk_overlap,
        )
        
        logger.info("Knowledge Base Service initialized successfully!")
    
    async def process_document(
        self,
        file_content: bytes,
        filename: str,
        collection_name: str = "documents",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process and index a document
        
        Args:
            file_content: Raw file content
            filename: Original filename
            collection_name: Qdrant collection name
            metadata: Additional metadata
            
        Returns:
            Dict containing processing results
        """
        try:
            temp_dir = Path(tempfile.gettempdir()) / "uploads"
            temp_dir.mkdir(exist_ok=True)
            original_filename = Path(filename)
            extension = original_filename.suffix
            
            # Create a unique temporary file with original extension
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=extension,
                dir=temp_dir
            )
            
            # Write content to temporary file
            with open(temp_file.name, 'wb') as f:
                f.write(file_content)
            
            file_info = FileResponse(
                file_path=temp_file.name,
                original_filename=original_filename.name,
                extension=extension,
                size=os.path.getsize(temp_file.name)
            )
            file_path = file_info["file_path"]
            
            documents = parse_multiple_files(
                str(file_path),
                extractor=self.file_extractor.get_extractor_for_file(file_path),
            )
            # Process with RAG Manager
            documents_id = []
            for doc in documents:
                documents_id.append(
                    self.rag_manager.process_document(
                        document=doc.text,
                        collection_name=collection_name,
                        metadata=doc.metadata
                    )
                )
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                print(f"Error cleaning up temporary file: {e}")
            return {
                "status": "success",
                "documents_id": documents_id,
                "total": len(documents_id),
                "collection": collection_name
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            raise
    
    async def query_documents(
        self,
        query: str,
        collection_name: str,
        limit: int = 5
    ) -> Dict[str, str]:
        """
        Query processed documents
        
        Args:
            query: Search query
            collection_name: Collection to search
            limit: Maximum number of results
            
        Returns:
            Dict containing response
        """
        try:
            response = self.rag_manager.search(
                query=query,
                collection_name=collection_name,
                limit=limit
            )
            return {"response": response}
            
        except Exception as e:
            logger.error(f"Error querying documents: {str(e)}")
            raise
    
    async def delete_document(
        self,
        collection_name: str,
        document_id: str
    ) -> Dict[str, str]:
        """
        Delete a document
        
        Args:
            collection_name: Collection name
            document_id: Document ID to delete
            
        Returns:
            Status message
        """
        try:
            self.rag_manager.delete_document(
                collection_name=collection_name,
                document_id=document_id
            )
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise