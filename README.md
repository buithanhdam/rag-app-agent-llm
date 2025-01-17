# agent-llm-rag-app
- This repository contains an implementation of agentic patterns such as **Planning (ReActAgent flow)** from [multi-agent](https://github.com/buithanhdam/multi-agent) and [kotaemon](https://github.com/Cinnamon/kotaemon)

## Introduction to RAG💡
Large Language Models are trained on a fixed dataset, which limits their ability to handle private or recent information. They can sometimes "hallucinate", providing incorrect yet believable answers. Fine-tuning can help but it is expensive and not ideal for retraining again and again on new data. The Retrieval-Augmented Generation (RAG) framework addresses this issue by using external documents to improve the LLM's responses through in-context learning. RAG ensures that the information provided by the LLM is not only contextually relevant but also accurate and up-to-date.

![final diagram](https://github.com/user-attachments/assets/508b3a87-ac46-4bf7-b849-145c5465a6c0)

There are four main components in RAG:

**Indexing:** First, documents (in any format) are split into chunks, and embeddings for these chunks are created. These embeddings are then added to a vector store.

**Retriever:** Then, the retriever finds the most relevant documents based on the user's query, using techniques like vector similarity from the vector store.

**Augment:** After that, the Augment part combines the user's query with the retrieved context into a prompt, ensuring the LLM has the information needed to generate accurate responses.

**Generate:** Finally, the combined query and prompt are passed to the model, which then generates the final response to the user's query.

These components of RAG allow the model to access up-to-date, accurate information and generate responses based on external knowledge. However, to ensure RAG systems are functioning effectively, it’s essential to evaluate their performance.

## Advanced RAG Techniques⚙️
Here are the details of all the Advanced RAG techniques covered in this repository.

| Technique       | Tools                                | Description                                                                                   |
|-----------------|--------------------------------------|-----------------------------------------------------------------------------------------------|
| Naive RAG       | LlamaIndex, Qdrant, Google Gemini    | Combines retrieved data with LLMs for simple and effective responses.                         |
| Hybrid RAG      | LlamaIndex, Qdrant, Google Gemini    | Combines vector search and traditional methods like BM25 for better information retrieval.     |
| Hyde RAG        | LlamaIndex, Qdrant, Google Gemini    | Combines hybrid RAG and creates hypothetical document embeddings to find relevant information. |
| RAG fusion      | LlamaIndex, LangSmith, Qdrant, Google Gemini | Generates sub-queries, ranks documents with Reciprocal Rank Fusion, and uses top results for accurate responses. |
| Contextual RAG  | LlamaIndex, Qdrant, Google Gemini, Anthropic | Compresses retrieved documents to keep only relevant details for concise and accurate responses. |
| Unstructured RAG | LlamaIndex, Qdrant, FAISS, Google Gemini, Unstructured | Designed to handle documents that combine text, tables, and images.                            |

---

## 1. Running Backend with Streamlit Separately

If you want to run the backend with Streamlit separately, please follow the instructions in the `README.md` file located in the `backend` folder

For detailed instructions, see: [backend/README.md](backend/README.md)

## 2. Running the Entire Project with Docker and Docker Compose

To run the entire project (including backend, frontend, and other services), you can use Docker and Docker Compose.

### Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)

### Steps

1. **Clone the Project**:

   ```bash
    git clone https://github.com/buithanhdam/rag-app-agent-llm.git
    cd rag-app-agent-llm
   ```

2. **Configure Environment Variables**:

   - Create `.env` files in the `backend` and `frontend` folders (if needed) and fill in the required environment variables. For example:
     ```bash
     cp ./frontend/.env.example ./frontend/.env
    cp ./backend/.env.example ./backend/.env
     ```
    ```plaintext
    #for backend .env
    GOOGLE_API_KEY=<your_google_api_key>
    OPENAI_API_KEY=<your_openai_api_key>
    ANTHROPIC_API_KEY=<your_anthropic_api_key>
    BACKEND_API_URL=http://localhost:8000
    QDRANT_URL=http://localhost:6333

    #for frontend .env
    NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
    ```
3. **Build and Run the Project**:

   ```bash
   docker-compose up --build
   ```

   This command will build and run all the services defined in `docker-compose.yml`.

4. **Access the Application**:

   - **Frontend**: Open your browser and go to `http://localhost:3000`.
   - **Backend**: The backend API will run on `http://localhost:8000`.
   - **Streamlit**: If applicable, Streamlit will run on `http://localhost:8501`.

5. **Stop the Project**:

   To stop all services, run:

   ```bash
   docker-compose down
   ```

## 3. Project Structure

- **backend/**: Contains the backend source code.
  - `README.md`: Instructions for running the backend with Streamlit separately.
  - `Dockerfile.backend`: Dockerfile for building the backend.
  - `requirements.txt`: Backend dependencies.

- **frontend/**: Contains the frontend source code.
  - `Dockerfile.frontend`: Dockerfile for building the frontend.
  - `next.config.js`: Next.js configuration.

- **docker-compose.yml**: Docker Compose configuration file for running the entire project.

- **Jenkinsfile**: Jenkins configuration file for CI/CD.