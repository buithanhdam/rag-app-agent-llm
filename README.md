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


## Project Structure

```
.
├── __pycache__
├── .theflow
├── api
├── data
├── docker
├── logs
├── src
├── venv
├── .env
├── .env.example
├── .gitignore
├── app_fastapi.py
├── app_streamlit.py
├── docker-compose.yaml
├── README.md
├── requirements_streamlit.txt
├── requirements.txt
```

### Explanation
- `api/`: Contains backend API logic for FastAPI.
- `data/`: Directory for data storage, including Qdrant storage.
- `docker/`: Docker configurations for backend and frontend services.
- `logs/`: Directory for log files.
- `src/`: Additional source code.
- `venv/`: Virtual environment for dependencies.
- `.env`: Environment variables file.
- `.gitignore`: Specifies files and directories to ignore in Git.
- `app_fastapi.py`: Main FastAPI application.
- `app_streamlit.py`: Main Streamlit application.
- `docker-compose.yaml`: Docker Compose configuration.
- `requirements.txt`: Backend dependencies.
- `requirements_streamlit.txt`: Streamlit frontend dependencies.

---

## Installation and Setup

### Prerequisites
- Install [Docker](https://docs.docker.com/get-docker/).
- Install [Git](https://git-scm.com/downloads).
- Use Python 3.9+.

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/buithanhdam/agent-llm-rag-app.git
   cd agent-llm-rag-app
   ```

2. **Set up the virtual environment**
- **For Unix/macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **For Windows:**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate
  ```
3. **Install dependencies**
   - Backend (FastAPI):
     ```bash
     pip install -r requirements.txt
     ```
   - Frontend (Streamlit):
     ```bash
     pip install -r requirements_streamlit.txt
     ```

---

## Setup Environment Variables

Copy the `.env.example` file to a new `.env` file and update the API keys:

```bash
cp .env.example .env
```

Add the following keys:

```plaintext
GOOGLE_API_KEY=<your_google_api_key>
OPENAI_API_KEY=<your_openai_api_key>
ANTHROPIC_API_KEY=<your_anthropic_api_key>
BACKEND_API_URL=http://localhost:8000
QDRANT_URL=http://localhost:6333
```

---

## Running the Application

### 1. Run FastAPI Backend

```bash
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

- Access the API at: `http://127.0.0.1:8000`

### 2. Run Streamlit Frontend

```bash
streamlit run app_streamlit.py --server.port=8501 --server.address=0.0.0.0
```

- Access the frontend UI at: `http://localhost:8501`

---

## Using Docker

### Build and Run Services
1. Ensure Docker is running on your system.
2. Use Docker Compose to build and start the containers.

   ```bash
   docker-compose build
   ```

   ```bash
   docker-compose up
   ```

### Services Included
- **fastapi**: Exposes port `8000`.
- **streamlit**: Exposes port `8501`.
- **qdrant**: Exposes ports `6333` and `6334`.

### Accessing Services
- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

### Stopping Services
To stop all running containers:
```bash
docker-compose down
```

### Additional Docker Information
- Docker network: `rag-app-network` (bridge).
- FastAPI service uses `./docker/Dockerfile.backend`.
- Streamlit service uses `./docker/Dockerfile.frontend`.

---

## Troubleshooting
- Ensure `.env` is correctly configured.
- Run `docker-compose up --build` if there are changes in the Docker configuration.
- Verify that all required ports are available (8000, 8501, 6333).

---

This documentation provides all necessary steps to set up, run, and manage the project efficiently.

