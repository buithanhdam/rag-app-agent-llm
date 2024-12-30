import os
import torch
import chromadb
import urllib.parse
import dotenv
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext,VectorStoreIndex,PropertyGraphIndex
from llama_index.core.schema import MetadataMode,ImageNode
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.graph_stores.kuzu import KuzuPropertyGraphStore
import kuzu
from src.constants import DOCUMENT_EMBEDDING_MODEL_NAME, DOCUMENT_EMBEDDING_SERVICE
# import re
import nest_asyncio 
nest_asyncio.apply()
dotenv.load_dotenv(override=True)

simple_content_template = """
Document: {paper_content}
"""

simple_image_content_template = """
Image URL: {image_url}
Document: {paper_content}
"""

simple_web_search_template = """
Title: {title}
Link: {search_link}
Content: {search_content}
"""

# print(tool_db['SOP']['db_path'])

def load_document_search_tool():
    device_type = torch.device("cuda" if torch.cuda.is_available() else "cpu") 
    if DOCUMENT_EMBEDDING_SERVICE == "openai":
        embed_model = OpenAIEmbedding(
            model=DOCUMENT_EMBEDDING_MODEL_NAME, 
            api_key=os.environ["OPENAI_API_KEY"])
    else:
        raise NotImplementedError()
    
    def load_concept_retriever(): 
        chroma_client = chromadb.PersistentClient(path=tool_db[bot_type]['db_path'])
        chroma_collection = chroma_client.get_or_create_collection("knowledge_vector_docs")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)    
        # load the vectorstore
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        paper_index = VectorStoreIndex.from_vector_store(vector_store, storage_context=storage_context, embed_model=embed_model)

        concept_retriever = paper_index.as_retriever(
            similarity_top_k=10,
        )
        return concept_retriever
    def load_graph_retriever(): 
        db = kuzu.Database(tool_db[bot_type]['db_path'])
        graph_store = KuzuPropertyGraphStore(db)
        llm = OpenAI(model="gpt-3.5-turbo", temperature=0.3)

        graph_index = PropertyGraphIndex.from_existing(
            embed_model=embed_model,
            llm = llm,
            property_graph_store=graph_store,
        )
        query_engine = graph_index.as_query_engine(
            include_text=False
        )
        return query_engine
    concept_retriever = load_concept_retriever()
    graph_retriever = load_graph_retriever()
    
    def retrieve_sop_guide(query_str: str):
        graph_retriever_response = graph_retriever.query(query_str)
        # print(graph_retriever_response)
        retriever_response =  concept_retriever.retrieve(str(graph_retriever_response))
        retriever_result = []
        for n in retriever_response:
            if isinstance(n.node, ImageNode):
                str_image = n.node.image_url
                str_image = str_image.replace("\n", "")
                text = simple_image_content_template.format(image_url=str_image,paper_content=n.node.metadata)
                retriever_result.append(text)
            else:
                file_name = n.node.metadata["file_name"]
                # paper_id = list(n.node.relationships.items())[0][1].node_id
                paper_content = n.node.get_content(metadata_mode=MetadataMode.LLM)
                paper_content = paper_content.replace('\n', '')

                file_name = file_name.split(".")[0]
        
                n.node.text = simple_content_template.format(
                        paper_content=paper_content
                )
                retriever_result.append(n.node.text)

        return retriever_result
            
        
    return FunctionTool.from_defaults(
        retrieve_sop_guide,
        # retrieve_epoint_guide,
        # description="Hỗ trợ các Dịch vụ trợ lý, hỗ trợ lỗi, truy xuất thông tin liên quan từ Hướng Dẫn Sử Dụng Sale online platform (SOP),"+
        # "bao gồm thông tin liên quan đến các bên thứ ba như facebook, zalo được hướng dẫn trong Sale online platform (SOP)."
        description=tool_db[bot_type]['description'] 
        )