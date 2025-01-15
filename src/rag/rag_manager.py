# rag_manager.py
from typing import Optional, Type
from src.logger import get_formatted_logger
from .base_rag import BaseRAGManager
from .normal_rag import NormalRAGManager
from .hybrid_rag import HybridRAGManager
from src.config import RAGType
logger = get_formatted_logger(__file__)


class RAGManager:
    """
    Factory class for managing different types of RAG implementations
    """
    _rag_implementations = {
        RAGType.NORMAL: NormalRAGManager,
        RAGType.HYBRID: HybridRAGManager,
        # Add other implementations as they are created
        # RAGType.CONTEXTUAL: ContextualRAGManager,
        # RAGType.FUSION: FusionRAGManager,
        # RAGType.HYDE: HydeRAGManager,
        # RAGType.NAIVE: NaiveRAGManager,
    }

    @classmethod
    def get_rag_implementation(
        cls,
        rag_type: RAGType
    ) -> Optional[Type[BaseRAGManager]]:
        """
        Get the RAG implementation class for a given RAG type
        
        Args:
            rag_type: The type of RAG implementation to get
            
        Returns:
            The RAG implementation class or None if not found
        """
        implementation = cls._rag_implementations.get(rag_type)
        if implementation is None:
            logger.warning(f"RAG type {rag_type} not implemented yet, falling back to normal RAG")
            implementation = cls._rag_implementations[RAGType.NORMAL]
        return implementation

    @classmethod
    def create_rag(
        cls,
        rag_type: RAGType,
        qdrant_url: str,
        gemini_api_key: str,
        **kwargs
    ) -> BaseRAGManager:
        """
        Create a new RAG instance of the specified type
        
        Args:
            rag_type: The type of RAG to create
            qdrant_url: URL for Qdrant server
            gemini_api_key: API key for Gemini
            **kwargs: Additional arguments to pass to the RAG implementation
            
        Returns:
            A new RAG instance
            
        Raises:
            ValueError: If the RAG type is not recognized
        """
        implementation = cls.get_rag_implementation(rag_type)
        if implementation is None:
            raise ValueError(f"Unsupported RAG type: {rag_type}")
            
        try:
            rag_instance = implementation(
                qdrant_url=qdrant_url,
                gemini_api_key=gemini_api_key,
                **kwargs
            )
            logger.info(f"Successfully created {rag_type.value} instance")
            return rag_instance
            
        except Exception as e:
            logger.error(f"Error creating RAG instance: {str(e)}")
            raise

    @classmethod
    def register_implementation(
        cls,
        rag_type: RAGType,
        implementation: Type[BaseRAGManager]
    ):
        """
        Register a new RAG implementation
        
        Args:
            rag_type: The type of RAG to register
            implementation: The implementation class
        """
        if not issubclass(implementation, BaseRAGManager):
            raise ValueError("Implementation must inherit from BaseRAGManager")
            
        cls._rag_implementations[rag_type] = implementation
        logger.info(f"Registered new implementation for {rag_type.value}")