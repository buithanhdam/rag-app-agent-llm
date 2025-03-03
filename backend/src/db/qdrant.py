import sys
from src.logger import get_formatted_logger
from pathlib import Path
import logging
from abc import ABC, abstractmethod
from qdrant_client.http import models
from qdrant_client import QdrantClient
from typing import List, Dict, Any, Optional
from qdrant_client.http.exceptions import ResponseHandlingException
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    after_log,
    before_sleep_log,
    retry_if_exception_type,
)

sys.path.append(str(Path(__file__).parent.parent.parent))
from qdrant_client.models import ScoredPoint
from src.config import QdrantPayload
from src.logger import get_formatted_logger
logger = get_formatted_logger(__file__)


class BaseVectorDatabase(ABC):
    @abstractmethod
    def check_collection_exists(self, collection_name: str):
        """
        Check if the collection exists

        Args:
            collection_name (str): Collection name to check
        """
        pass

    @abstractmethod
    def test_connection(self):
        """
        Test the connection with the server.
        """
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, vector_size: int):
        """
        Create a new collection

        Args:
            collection_name (str): Collection name
            vector_size (int): Vector size
        """
        pass

    @abstractmethod
    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ):
        """
        Add a vector to the collection

        Args:
            collection_name (str): Collection name to add
            vector_id (str): Vector ID
            vector (List[float]): Vector embedding
            payload (Dict[str, Any]): Payload for the vector
        """
        pass


class QdrantVectorDatabase(BaseVectorDatabase):
    """
    QdrantVectorDatabase client
    """

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_fixed(5),
        after=after_log(logger, logging.DEBUG),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        retry=retry_if_exception_type(ConnectionError),
    )
    def __init__(self, url: str, distance: str = models.Distance.COSINE) -> None:
        self.url = url
        self.client = QdrantClient(url)
        self.distance = distance
        self.test_connection()

        logger.info("Qdrant client initialized successfully !!!")

    def test_connection(self):
        """
        Test the connection with the Qdrant server.
        """
        try:
            self.client.get_collections()
        except ResponseHandlingException:
            raise ConnectionError("Qdrant connection failed")

    def check_collection_exists(self, collection_name: str):
        return self.client.collection_exists(collection_name)

    def create_collection(self, collection_name: str, vector_size: int = 768):
        if not self.client.collection_exists(collection_name):
            logger.info(f"Creating collection {collection_name}")
            self.client.create_collection(
                collection_name,
                vectors_config={
                    "dense": models.VectorParams(
                        size=vector_size,
                        distance=self.distance
                        ),
                    "late-interaction": models.VectorParams(
                        size=vector_size,
                        distance=self.distance,
                        multivector_config=models.MultiVectorConfig(
                            comparator=models.MultiVectorComparator.MAX_SIM
                        ),
                    )
                },
                sparse_vectors_config={
                    "sparse": models.SparseVectorParams(
                        size=vector_size,
                        distance=self.distance
                        )
                },
                optimizers_config=models.OptimizersConfigDiff(
                    default_segment_number=5,
                    indexing_threshold=0,
                ),
                quantization_config=models.BinaryQuantization(
                    binary=models.BinaryQuantizationConfig(always_ram=True),
                ),
            )

    def add_vector(
        self,
        collection_name: str,
        vector_id: str,
        vector: List[float],
        payload: QdrantPayload,
    ):
        """
        Add a vector to the collection

        Args:
            collection_name (str): Collection name to add
            vector_id (str): Vector ID
            vector (List[float]): Vector embedding
            payload (QdrantPayload): Payload for the vector
        """
        if not self.check_collection_exists(collection_name):
            self.create_collection(collection_name, len(vector))

        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=vector_id,
                    payload=payload.model_dump(),
                    vector=vector,
                )
            ],
        )

    def delete_vector(self, collection_name: str, document_id: str|int):
        """
        Delete a vector from the collection

        Args:
            collection_name (str): Collection name to delete
            document_id (str | UUID): Document ID to delete
        """

        if not self.check_collection_exists(collection_name):
            logger.debug(f"Collection {collection_name} does not exist")
            return

        logger.debug(
            "collection_name: %s - document_id: %s", collection_name, document_id
        )

        self.client.delete(
            collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    def delete_collection(self, collection_name: str):
        """
        Delete a collection

        Args:
            collection_name (str): Collection name to delete
        """
        if not self.check_collection_exists(collection_name):
            logger.debug(f"Collection {collection_name} does not exist")
            return

        success = self.client.delete_collection(collection_name)

        if success:
            logger.debug(f"Collection {collection_name} deleted successfully!")

    
    def search_vector(
        self,
        collection_name: str,
        vector: list[float] | list[list[float]],
        search_params: models.SearchParams,
        limit :int,
    ) -> List[ScoredPoint]:
        """
        Search for a vector in the collection
        Args:
            collection_name (str): Collection name to search
            vector (list[float]): Vector embedding
            search_params (models.SearchParams): Search parameters
        Returns:
            List[models.PointStruct]: List of points
        """
        
        if isinstance(vector, list) and all(isinstance(x, (int, float)) for x in vector):
            vector = [vector]
            
        return self.client.query_points(
            collection_name=collection_name,
            query=vector,
            search_params=search_params,
            using="late-interaction",
            with_payload=True,
            limit=limit
        ).points
    
    # def hybrid_search_vector(
    #     self,
    #     collection_name: str,
    #     vectors: list[float] | list[list[float]],
    #     search_params: models.SearchParams,
    #     limit :int,
    # ) -> List[ScoredPoint]:
    #     """
    #     Hybrid Search for a vector in the collection
    #     Args:
    #         collection_name (str): Collection name to search
    #         vector (list[float]): Vector embedding
    #         search_params (models.SearchParams): Search parameters
    #     Returns:
    #         List[models.PointStruct]: List of points
    #     """
    #     if isinstance(vectors, list) and all(isinstance(x, (int, float)) for x in vectors):
    #         vectors = [vectors]
    #     matryoshka_prefetch = models.Prefetch(
    #         prefetch=[
    #             models.Prefetch(
    #                 prefetch=[
    #                     # The first prefetch operation retrieves 100 documents
    #                     # using the Matryoshka embeddings with the lowest
    #                     # dimensionality of 64.
    #                     models.Prefetch(
    #                         query=[0.456, -0.789, ..., 0.239],
    #                         using="matryoshka-64dim",
    #                         limit=100,
    #                     ),
    #                 ],
    #                 # Then, the retrieved documents are re-ranked using the
    #                 # Matryoshka embeddings with the dimensionality of 128.
    #                 query=[0.456, -0.789, ..., -0.789],
    #                 using="matryoshka-128dim",
    #                 limit=50,
    #             )
    #         ],
    #         # Finally, the results are re-ranked using the Matryoshka
    #         # embeddings with the dimensionality of 256.
    #         query=[0.456, -0.789, ..., 0.123],
    #         using="matryoshka-256dim",
    #         limit=25,
    #     )
    #     sparse_dense_rrf_prefetch = models.Prefetch(
    #         prefetch=[
    #             models.Prefetch(
    #                 prefetch=[
    #                     # The first prefetch operation retrieves 100 documents
    #                     # using dense vectors using integer data type. Retrieval
    #                     # is faster, but quality is lower.
    #                     models.Prefetch(
    #                         query=[7, 63, ..., 92],
    #                         using="dense-uint8",
    #                         limit=100,
    #                     )
    #                 ],
    #                 # Integer-based embeddings are then re-ranked using the
    #                 # float-based embeddings. Here we just want to retrieve
    #                 # 25 documents.
    #                 query=[-1.234, 0.762, ..., 1.532],
    #                 using="dense",
    #                 limit=25,
    #             ),
    #             # Here we just add another 25 documents using the sparse
    #             # vectors only.
    #             models.Prefetch(
    #                 query=models.SparseVector(
    #                     indices=[125, 9325, 58214],
    #                     values=[-0.164, 0.229, 0.731],
    #                 ),
    #                 using="sparse",
    #                 limit=25,
    #             ),
    #         ],
    #         # RRF is activated below, so there is no need to specify the
    #         # query vector here, as fusion is done on the scores of the
    #         # retrieved documents.
    #         query=models.FusionQuery(
    #             fusion=models.Fusion.RRF,
    #         ),
    #     )
    #     return self.client.query_points(
    #         collection_name=collection_name,
    #         prefetch=[
    #             matryoshka_prefetch,
    #             sparse_dense_rrf_prefetch,
    #         ],
    #         using="late-interaction",
    #         query=vectors,
    #         search_params=search_params,
    #         with_payload=True,
    #         limit=limit
    #     ).points