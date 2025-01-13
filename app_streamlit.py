import os
import streamlit as st
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8000')

st.set_page_config(
    page_title="Chat & Document Processing",
    layout="wide"
)

def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []

def add_message(role: str, content: str):
    st.session_state.messages.append({"role": role, "content": content})

def get_agent_response(prompt: str) -> str:
    try:
        full_url = f"{API_URL}/agent/chat"
        response = requests.post(full_url, json={"query": prompt})
        response.raise_for_status()
        return response.json()['response']
    except requests.RequestException as e:
        st.error(f"Error communicating with agent: {e}")
        return "Sorry, there was an error processing your request."

def reset_chat_history():
    try:
        full_url = f"{API_URL}/agent/reset"
        response = requests.post(full_url)
        response.raise_for_status()
        st.session_state.messages = []
        st.success("Chat history has been reset successfully!")
    except requests.RequestException as e:
        st.error(f"Error resetting chat history: {e}")

def upload_document(file, collection_name: str) -> Optional[dict]:
    try:
        files = {"file": file}
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            params={"collection_name": collection_name}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Upload failed: {str(e)}")
        return None

# def query_documents(query: str, collection_name: str, limit: int = 5) -> Optional[dict]:
#     try:
#         response = requests.post(
#             f"{API_URL}/query",
#             json={"query": query, "collection_name": collection_name, "limit": limit}
#         )
#         response.raise_for_status()
#         return response.json()
#     except Exception as e:
#         st.error(f"Query failed: {str(e)}")
#         return None

def main():
    st.title("Chat & Document Processing System")

    tab1, tab2 = st.tabs(["💬 Chat Interface", "📄 Document Processing"])

    with tab1:
        st.header("Agent Chat Interface")
        initialize_session_state()

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("What would you like to know?"):
            add_message("user", prompt)
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_agent_response(prompt)
                    st.markdown(response)
                    add_message("assistant", response)

        with st.sidebar:
            if st.button("🔄 Reset Chat", type="primary"):
                if st.checkbox("Confirm reset chat", key="confirm_reset"):
                    reset_chat_history()
                    st.experimental_rerun()

    with tab2:
        st.header("Document Processing")
        collection_name = st.sidebar.text_input("Collection Name", "documents")
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])

        if uploaded_file and st.button("Process Document"):
            with st.spinner("Processing..."):
                result = upload_document(uploaded_file, collection_name)
                if result:
                    st.success("Document processed successfully!")
                    st.json(result)

        # query = st.text_area("Enter your question about documents")
        # limit = st.slider("Number of results", 1, 10, 5)
        # if query and st.button("Search Documents"):
        #     with st.spinner("Searching..."):
        #         result = query_documents(query, collection_name, limit)
        #         if result:
        #             st.markdown("### Answer:")
        #             st.write(result["response"])

if __name__ == "__main__":
    main()
