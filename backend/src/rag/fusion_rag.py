from typing import List, Optional, Dict
import uuid
from tqdm import tqdm
from llama_index.core import Document
from qdrant_client.http import models
from qdrant_client.models import ScoredPoint
from src.config import QdrantPayload
from src.logger import get_formatted_logger
from .base_rag import BaseRAGManager
from llama_index.core import PromptTemplate
from llama_index.retrievers.bm25 import BM25Retriever
import Stemmer
from llama_index.core.schema import NodeWithScore

logger = get_formatted_logger(__file__)


class FusionRAG(BaseRAGManager):
    """
    Fusion RAG implementation using vector search, generate sub-queries and re-rank document score
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def process_document(
        self,
        document: str,
        collection_name: str,
        document_id: Optional[str] | Optional[int] = None,
        metadata: Optional[dict] = None,
        show_progress: bool = True,
    ) -> List[Document]:
        if document_id is None:
            document_id = str(uuid.uuid4())

        try:
            doc = Document(text=document, metadata=metadata or {})
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
                    payload=payload,
                )
                chunk.metadata["embedding"] = embedding

                logger.info(
                    f"Successfully processed document {document_id} with chunk {chunk.metadata['chunk_id']}"
                )
            return chunks_iter

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def fuse_rerank(
        self, nodes_with_scores: List[NodeWithScore], similarity_top_k: int = 2
    ):
        """Fuse results."""
        k = 60.0  # `k` is a parameter used to control the impact of outlier rankings.
        fused_scores = {}
        text_to_node = {}

        # compute reciprocal rank scores
        for rank, node_with_score in enumerate(
            sorted(nodes_with_scores, key=lambda x: x.score or 0.0, reverse=True)
        ):
            text = node_with_score.node.get_content()
            text_to_node[text] = node_with_score
            if text not in fused_scores:
                fused_scores[text] = 0.0
            fused_scores[text] += 1.0 / (rank + k)

        # sort results
        reranked_results = dict(
            sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        )

        # adjust node scores
        reranked_nodes: List[NodeWithScore] = []
        for text, score in reranked_results.items():
            reranked_nodes.append(text_to_node[text])
            reranked_nodes[-1].score = score

        return reranked_nodes[:similarity_top_k]

    def search(
        self,
        query: str,
        collection_name: str = "documents",
        limit: int = 5,
        score_threshold: int = 0.5,
    ) -> str:
        try:
            # Step 1: Generate sub-queries from user query
            query_gen_prompt_str = (
                "You are a helpful assistant that generates multiple search queries based on a "
                "single input query. Generate {num_queries} search queries, one on each line, "
                "related to the following input query:\n"
                "Query: {query}\n"
                "Queries:\n"
            )
            query_gen_prompt = PromptTemplate(query_gen_prompt_str)
            fmt_prompt = query_gen_prompt.format(num_queries=2, query=query)
            response = self.llm.complete(fmt_prompt)
            queries = response.text.split("\n")
            queries.remove("")  # Remove empty string
            queries.append(query)
            logger.info(f"Generated sub-queries: {queries}")

            # Step 2: Convert sub-queries and user query to embedding
            results: List[NodeWithScore] = []
            sub_query_embeddings = self.embedding_model.aget_text_embedding_batch(queries)
            
            # Step 3: Perform vector search using query embedding
            sub_query_results = self.qdrant_client.search_vector(
                collection_name=collection_name,
                vector=sub_query_embeddings,
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
                sub_query_results, score_threshold=score_threshold
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
                results.extend(bm25_results)

            contexts = self.fuse_rerank(results, similarity_top_k=limit)
            logger.info(f"contexts: {contexts}")
            # Step 4: Generate final response
            prompt = f"""Given the following context and question, provide a comprehensive answer based solely on the provided context. If the context doesn't contain relevant information, say so.

            Context:
            {' '.join([node.node.get_content() for node in contexts])}

            Question:
            {query}

            Answer:"""

            response = self.llm.complete(prompt).text
            return response

        except Exception as e:
            logger.error(f"Error during search: {str(e)}")
            raise

    def delete_document(self, collection_name: str, document_id: str):
        self.qdrant_client.delete_vector(
            collection_name=collection_name, document_id=document_id
        )
        logger.info(f"Deleted document {document_id}")
