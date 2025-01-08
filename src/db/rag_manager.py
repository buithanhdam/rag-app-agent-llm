import sys
from pathlib import Path
from typing import List, Optional
import uuid
from tqdm import tqdm
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.node_parser import SimpleNodeParser

from src.db.qdrant import QdrantVectorDatabase
from config import QdrantPayload
from src.logger import get_formatted_logger

logger = get_formatted_logger(__file__)

class RAGManager:
    """
    Basic RAG Manager class to handle document processing and retrieval using Qdrant
    """
    def __init__(
        self,
        qdrant_url: str,
        gemini_api_key: str,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
    ):
        """
        Initialize RAG Manager

        Args:
            qdrant_url: URL for Qdrant server
            gemini_api_key: API key for Google's Gemini
            chunk_size: Size of text chunks for splitting
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize Gemini models
        self.llm = Gemini(
            api_key=gemini_api_key,
            temperature=0.1
        )
        self.embedding_model = GeminiEmbedding(
            api_key=gemini_api_key
        )
        
        # Set global settings
        Settings.llm = self.llm
        Settings.embed_model = self.embedding_model
        Settings.chunk_size = chunk_size
        Settings.chunk_overlap = chunk_overlap
        
        # Initialize document parser
        self.parser = SimpleNodeParser.from_defaults()
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantVectorDatabase(url=qdrant_url)
        
        logger.info("RAG Manager initialized successfully!")

    def process_document(
        self,
        document: str,
        collection_name: str,
        document_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        show_progress: bool = True
    ) -> str:
        """
        Process and index a document
        
        Args:
            document: Document text content
            collection_name: Name of the Qdrant collection
            document_id: Optional document ID (will generate if not provided)
            metadata: Optional metadata for the document
            show_progress: Whether to show progress bars
            
        Returns:
            document_id: ID of the processed document
        """
        if document_id is None:
            document_id = str(uuid.uuid4())
            
        try:
            # Create document object
            doc = Document(
                text=document,
                metadata=metadata or {}
            )
            
            # Split into chunks
            chunks = self.split_document(doc, show_progress=show_progress)
            
            # Process and store chunks
            self.index_chunks(
                chunks=chunks,
                collection_name=collection_name,
                document_id=document_id,
                show_progress=show_progress
            )
            
            logger.info(f"Successfully processed document {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def split_document(
        self,
        document: Document,
        show_progress: bool = True
    ) -> List[Document]:
        """
        Split document into chunks
        
        Args:
            document: Document to split
            show_progress: Whether to show progress bar
            
        Returns:
            List of document chunks
        """
        nodes = self.parser.get_nodes_from_documents([document])
        
        chunks = []
        nodes_iter = tqdm(nodes, desc="Splitting...") if show_progress else nodes
        
        for node in nodes_iter:
            # Generate unique ID for each chunk
            chunk_id = str(uuid.uuid4())
            
            chunk = Document(
                text=node.get_content(),
                metadata={
                    **document.metadata,
                    "chunk_id": chunk_id
                }
            )
            chunks.append(chunk)
            
        return chunks

    def index_chunks(
        self,
        chunks: List[Document],
        collection_name: str,
        document_id: str,
        show_progress: bool = True
    ):
        """
        Index document chunks into Qdrant
        
        Args:
            chunks: List of document chunks
            collection_name: Qdrant collection name
            document_id: Document ID
            show_progress: Whether to show progress bar
        """
        chunks_iter = tqdm(chunks, desc="Indexing chunks...") if show_progress else chunks
        
        for chunk in chunks_iter:
            # Get embeddings
            embedding = self.embedding_model.get_text_embedding(
                chunk.text
            )
            
            # Create payload
            payload = QdrantPayload(
                document_id=document_id,
                text=chunk.text,
                vector_id=chunk.metadata["chunk_id"],
            )
            
            # Add to Qdrant
            self.qdrant_client.add_vector(
                collection_name=collection_name,
                vector_id=chunk.metadata["chunk_id"],
                vector=embedding,
                payload=payload
            )

    def search(
        self,
        query: str,
        collection_name: str,
        limit: int = 5
    ) -> str:
        """
        Search for relevant documents and generate response
        
        Args:
            query: Search query
            collection_name: Qdrant collection name
            kb_ids: List of knowledge base IDs to search in
            limit: Number of results to return
            
        Returns:
            Generated response based on retrieved context
        """
        try:
            # Get query embedding
            query_embedding = self.embedding_model.get_text_embedding(query)
            
            # Search Qdrant
            results = self.qdrant_client.search_vector(
                collection_name=collection_name,
                vector=query_embedding,
                limit=limit
            )
            
            # Extract contexts
            contexts = [result.payload["text"] for result in results]
            
            # Build prompt
            prompt = f"""Given the following context and question, provide a comprehensive answer based solely on the provided context. If the context doesn't contain relevant information, say so.

Context:
{' '.join(contexts)}

Question:
{query}

Answer:"""
            
            # Generate response
            response = self.llm.complete(prompt).text
            
            return response
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise

    def delete_document(self, collection_name: str, document_id: str):
        """
        Delete a document and its chunks from the vector database
        
        Args:
            collection_name: Qdrant collection name 
            document_id: ID of document to delete
        """
        self.qdrant_client.delete_vector(
            collection_name=collection_name,
            document_id=document_id
        )
        logger.info(f"Deleted document {document_id}")