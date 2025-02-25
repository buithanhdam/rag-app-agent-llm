from llama_index.core.tools import FunctionTool
from src.db.models import KnowledgeBase,RAGConfig, RAGType
from src.config import Settings
from typing import List

class RAGToolManager:
    @staticmethod
    def create_rag_tool_for_knowledge_base(knowledge_base: KnowledgeBase) -> FunctionTool:
        """Create a RAG function tool for a specific knowledge base"""
        settings = Settings()
        
        # Get RAG config from knowledge base
        rag_config:RAGConfig = knowledge_base.rag_config
        rag_type = rag_config.rag_type
        
        # Create a function that will search specifically in this knowledge base
        def search_kb(query: str, limit: int = 5) -> str:
            """
            Search through knowledge base and return relevant information
            
            Args:
                query: Search query
                limit: Maximum number of results to return
            """
            from src.rag.rag_manager import RAGManager
            
            rag_manager = RAGManager.create_rag(
                rag_type=rag_type,
                qdrant_url=settings.QDRANT_URL,
                gemini_api_key=settings.GEMINI_CONFIG.api_key,
                chunk_size=rag_config.chunk_size,
                chunk_overlap=rag_config.chunk_overlap,
            )
            
            # Use knowledge_base.specific_id as collection name or other identifier
            collection_name = knowledge_base.specific_id
            
            return rag_manager.search(
                query=query, 
                collection_name=collection_name,
                limit=limit
            )
        
        # Create function tool with proper name and description
        return FunctionTool.from_defaults(
            name=f"search_{knowledge_base.name.lower().replace(' ', '_')}",
            description=f"Search through the '{knowledge_base.name}' knowledge base: {knowledge_base.description}",
            fn=search_kb
        )
    
    @staticmethod
    def create_rag_tools_for_agent(knowledge_bases: List[KnowledgeBase]) -> List[FunctionTool]:
        """Create RAG tools for all knowledge bases associated with an agent"""
        return [
            RAGToolManager.create_rag_tool_for_knowledge_base(kb) 
            for kb in knowledge_bases
        ]