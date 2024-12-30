from typing import List, Dict, Any, Optional
from pathlib import Path
from uuid import uuid4

from doclingib import DocReader
from llama_index import Document
from qdrant_client.http import models
from qdrant_client.models import Distance

from src.db.qdrant import QdrantVectorDatabase
from src.constants import QdrantPayload
from src.logger import get_formatted_logger

logger = get_formatted_logger(__file__)

class RAGManager:
    """
    RAG Manager class to handle document processing and vector storage
    """
    def __init__(
        self,
        qdrant_url: str,
        collection_name: str,
        embedding_model: Any,  # You can specify your embedding model type
        distance: str = Distance.COSINE,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ):
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize Vector DB
        self.vector_db = QdrantVectorDatabase(
            url=qdrant_url,
            distance=distance
        )
        
        # Initialize DocLing reader
        self.doc_reader = DocReader()

    def process_document(
        self,
        file_path: str | Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a document and store its chunks in the vector database
        
        Args:
            file_path: Path to the document
            metadata: Additional metadata for the document
            
        Returns:
            document_id: Unique identifier for the processed document
        """
        # Generate document ID
        document_id = str(uuid4())
        
        try:
            # Read document using DocLing
            doc_content = self.doc_reader.read(file_path)
            
            # Create document object
            document = Document(
                text=doc_content,
                metadata=metadata or {}
            )
            
            # Split document into chunks
            chunks = self._split_document(document)
            
            # Process and store chunks
            for chunk_idx, chunk in enumerate(chunks):
                # Generate embeddings
                embedding = self.embedding_model.encode(chunk.text)
                
                # Prepare payload
                payload = QdrantPayload(
                    document_id=document_id,
                    chunk_index=chunk_idx,
                    text=chunk.text,
                    metadata=chunk.metadata
                )
                
                # Store in vector database
                self.vector_db.add_vector(
                    collection_name=self.collection_name,
                    vector_id=f"{document_id}_{chunk_idx}",
                    vector=embedding.tolist(),
                    payload=payload
                )
            
            logger.info(f"Successfully processed document {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def _split_document(self, document: Document) -> List[Document]:
        """
        Split document into chunks
        
        Args:
            document: Document to split
            
        Returns:
            List of document chunks
        """
        # You can implement your own chunking logic here
        # For now, using a simple character-based split
        text_chunks = []
        start = 0
        
        while start < len(document.text):
            end = start + self.chunk_size
            if end < len(document.text):
                # Find the last period or newline before the chunk size
                last_period = document.text.rfind('.', start, end)
                last_newline = document.text.rfind('\n', start, end)
                split_point = max(last_period, last_newline)
                
                if split_point > start:
                    end = split_point + 1
            
            chunk_text = document.text[start:end]
            chunk = Document(
                text=chunk_text,
                metadata=document.metadata.copy()
            )
            text_chunks.append(chunk)
            
            start = end - self.chunk_overlap

        return text_chunks

    def search(
        self,
        query: str,
        limit: int = 5,
        search_params: Optional[models.SearchParams] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            kb_ids: List of knowledge base IDs to search in
            limit: Maximum number of results to return
            search_params: Additional search parameters
            
        Returns:
            List of search results with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Set default search parameters if none provided
        if search_params is None:
            search_params = models.SearchParams(
                hnsw_ef=128,
                exact=False
            )
        
        # Search in vector database
        results = self.vector_db.search_vector(
            collection_name=self.collection_name,
            vector=query_embedding.tolist(),
            search_params=search_params,
            limit=limit
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.payload.get("text", ""),
                "score": result.score,
                "document_id": result.payload.get("document_id", ""),
                "metadata": result.payload.get("metadata", {})
            })
            
        return formatted_results

    def delete_document(self, document_id: str):
        """
        Delete a document and its chunks from the vector database
        
        Args:
            document_id: ID of the document to delete
        """
        self.vector_db.delete_vector(
            collection_name=self.collection_name,
            document_id=document_id
        )
        logger.info(f"Deleted document {document_id}")