# src/services/kb.py
from pathlib import Path
from typing import Optional, Dict, Any
from src.readers.docling import DoclingReader
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
        self.reader = DoclingReader(
            num_threads=settings.READER_CONFIG.num_threads,
            image_resolution_scale=settings.READER_CONFIG.image_resolution_scale,
            enable_ocr=settings.READER_CONFIG.enable_ocr,
            enable_tables=settings.READER_CONFIG.enable_tables
        )
        
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
            # Process with DoclingReader
            doc_result = self.reader.process_bytes(
                file_bytes=file_content,
                file_extension=Path(filename).suffix
            )
            
            # Merge provided metadata with file metadata
            combined_metadata = {
                "filename": filename,
                "num_pages": doc_result["metadata"]["num_pages"]
            }
            if metadata:
                combined_metadata.update(metadata)
            
            # Process with RAG Manager
            document_id = self.rag_manager.process_document(
                document=doc_result["markdown_content"],
                collection_name=collection_name,
                metadata=combined_metadata,
                show_progress=False  # Disable progress bars for API
            )
            
            return {
                "status": "success",
                "document_id": document_id,
                "pages": len(doc_result["pages"]),
                "collection": collection_name,
                "metadata": combined_metadata
            }
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
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