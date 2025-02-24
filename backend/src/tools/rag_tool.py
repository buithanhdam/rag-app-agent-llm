from src.rag.rag_manager import RAGManager
from src.config import Settings
from src.db.models import RAGType
# Example RAG Tool implementation
def retrieve_documents(query: str) -> str:
    """
    Search through knowledge base about customer service and return relevant information
            
    Args:
        query: Search query
    """
    settings = Settings()
    rag_manager = RAGManager.create_rag(
            rag_type=RAGType.HYBRID,
            qdrant_url=settings.QDRANT_URL,
            gemini_api_key=settings.GEMINI_CONFIG.api_key,
            chunk_size=settings.RAG_CONFIG.chunk_size,
            chunk_overlap=settings.RAG_CONFIG.chunk_overlap,
        )
    def search_documents(query: str, collection_name: str = "documents", limit: int = 5) -> str:
        return rag_manager.search(query=query, collection_name=collection_name,limit=limit)
    
    return search_documents(query=query)
    