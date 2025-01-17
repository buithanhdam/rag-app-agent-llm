from typing import List, Optional, Dict
import uuid
from tqdm import tqdm
from llama_index.core import Document
from qdrant_client.http import models
from src.config import QdrantPayload
from src.logger import get_formatted_logger
from .base_rag import BaseRAGManager
logger = get_formatted_logger(__file__)

class NaiveRAG(BaseRAGManager):
    """
    Standard RAG implementation using vector search
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.document_store: Dict[str, List[Document]] = {}
    def process_document(
        self,
        document: str,
        collection_name: str,
        document_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        show_progress: bool = True
    ) -> str:
        if document_id is None:
            document_id = str(uuid.uuid4())
            
        try:
            doc = Document(
                text=document,
                metadata=metadata or {}
            )
            chunks = self.split_document(doc, show_progress=show_progress)
            
            # Index chunks
            chunks_iter = tqdm(chunks, desc="Indexing...") if show_progress else chunks
            for chunk in chunks_iter:
                embedding = self.embedding_model.get_text_embedding(chunk.text)
                
                # Ensure collection exists
                if chunk == chunks[0]:  # Only check on first chunk
                    self.ensure_collection(collection_name, len(embedding))
                
                payload = QdrantPayload(
                    document_id=document_id,
                    text=chunk.text,
                    vector_id=chunk.metadata["chunk_id"],
                )
                
                self.qdrant_client.add_vector(
                    collection_name=collection_name,
                    vector_id=chunk.metadata["chunk_id"],
                    vector=embedding,
                    payload=payload
                )
            
            logger.info(f"Successfully processed document {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def search(
        self,
        query: str,
        collection_name: str = "documents",
        limit: int = 5,
        score_threshold: int =0.5
    ) -> str:
        try:
            
            # Step 1: Convert user query to embedding
            query_embedding = self.embedding_model.get_text_embedding(query)
            
            # Step 2: Perform vector search using query embedding
            results = self.qdrant_client.search_vector(
                collection_name=collection_name,
                vector=query_embedding,
                limit=limit,
                search_params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        ignore=False,
                        rescore=True,
                        oversampling=2.0,
                    )
                ),
            )
            
            contexts = [result.payload["text"] for result in results]
            
            # Step 3: Generate final response
            prompt = f"""Given the following context and question, provide a comprehensive answer based solely on the provided context. If the context doesn't contain relevant information, say so.

Context:
{' '.join(contexts)}

Question:
{query}

Answer:"""
            
            response = self.llm.complete(prompt).text
            return response
            
        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise

    def delete_document(
        self,
        collection_name: str,
        document_id: str
    ):
        self.qdrant_client.delete_vector(
            collection_name=collection_name,
            document_id=document_id
        )
        logger.info(f"Deleted document {document_id}")