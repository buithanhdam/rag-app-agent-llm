from typing import List, Optional
import uuid
from tqdm import tqdm
from qdrant_client.http import models
from llama_index.core import Document
from llama_index.retrievers.bm25 import BM25Retriever
from src.config import QdrantPayload
from src.logger import get_formatted_logger
from .base_rag import BaseRAGManager
import Stemmer
from llama_index.core.node_parser import SentenceSplitter

logger = get_formatted_logger(__file__)

class HybridRAG(BaseRAGManager):
    """
    Hybrid RAG implementation combining vector search and BM25 using Qdrant directly
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def convert_scored_points_to_nodes(
        self,
        scored_points: List[models.ScoredPoint],
        score_threshold: float = 0.0
    ) -> List[Document]:
        """
        Convert Qdrant ScoredPoint results to LlamaIndex nodes
        
        Args:
            scored_points: List of Qdrant search results
            score_threshold: Minimum score threshold for including results
            
        Returns:
            List of LlamaIndex BaseNode objects
        """
        docs = []
        
        for point in scored_points:
            if point.score < score_threshold:
                continue
                
            # Create node with text and metadata
            doc = Document(
                text=point.payload.get("text", ""),
                metadata={
                    "document_id": point.payload.get("document_id"),
                    "vector_id": point.payload.get("vector_id"),
                    "score": point.score,
                    # Add any other metadata from payload
                    **{k: v for k, v in point.payload.items() 
                    if k not in ["text", "document_id", "vector_id"]}
                }
            )
            
            docs.append(doc)
                # initialize node parser
        splitter = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

        nodes = splitter.get_nodes_from_documents(docs)
            
        return nodes
    def process_document(
        self,
        document: str,
        collection_name: str,
        document_id: Optional[str] | Optional[int] = None,
        metadata: Optional[dict] = None,
        show_progress: bool = True
    ) -> List[Document]:
        if document_id is None:
            document_id = str(uuid.uuid4())
            
        try:
            # Process document for vector search
            doc = Document(
                text=document,
                metadata=metadata or {}
            )
            chunks = self.split_document(doc, show_progress=show_progress)
            
            # Index for vector search
            chunks_iter = tqdm(chunks, desc="Indexing...") if show_progress else chunks
            for chunk in chunks_iter:
                embedding = self.embedding_model.get_text_embedding(chunk.text)
                
                # Ensure collection exists
                if chunk == chunks[0]:
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
                chunk.metadata["embedding"] = embedding
            
                logger.info(f"Successfully processed document {document_id} with chunk {chunk.metadata['chunk_id']}")
            return chunks_iter
            
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
            normal_results = self.qdrant_client.search_vector(
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
            logger.info(normal_results)
            
            # Step 3: BM25 retrieval
            bm25_points = self.qdrant_client.search_vector(
                collection_name=collection_name,
                vector=query_embedding,
                limit=50,
                search_params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(
                        ignore=False,
                        rescore=True,
                        oversampling=2.0,
                    )
                ),
            )
            doc_nodes = self.convert_scored_points_to_nodes(
                bm25_points,
                score_threshold=score_threshold
            )
            if doc_nodes:
                ## Perform BM25 search
                bm25_retriever = BM25Retriever.from_defaults(
                    nodes=doc_nodes,
                    similarity_top_k=limit,
                    stemmer=Stemmer.Stemmer("english"),
                    language="english",
                )
                bm25_results = bm25_retriever.retrieve(query)
                logger.info(bm25_results)
                
                # Step 4: Combine results
                all_texts = set()
                contexts = []
                
                ## Add vector search results
                for result in normal_results:
                    text = result.payload["text"]
                    if text not in all_texts:
                        contexts.append(text)
                        all_texts.add(text)
                
                ## Add BM25 results
                for node in bm25_results:
                    text = node.get_content()
                    if text not in all_texts and len(contexts) < limit:
                        contexts.append(text)
                        all_texts.add(text)
            else:
                contexts = [result.payload["text"] for result in normal_results]
            
            # Step 5: Generate final response
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