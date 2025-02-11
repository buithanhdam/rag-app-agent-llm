# Agent-LLM-RAG-App

- This repository contains an implementation of agentic patterns such as **Planning (ReActAgent flow)** from [multi-agent](https://github.com/buithanhdam/multi-agent) and [kotaemon](https://github.com/Cinnamon/kotaemon)

## Table of Contents

1. [Introduction to RAG](#1-introduction-to-rag)
2. [Advanced RAG Techniques](#2-advanced-rag-techniques)
3. [Running Backend with Streamlit Separately](#3-running-backend-with-streamlit-separately)
4. [Running the Entire Project with Docker and Docker Compose](#4-running-the-entire-project-with-docker-and-docker-compose)
5. [Project Structure](#5-project-structure)

---

## 1. Introduction to RAG 💡

Large Language Models are trained on a fixed dataset, which limits their ability to handle private or recent information. They can sometimes "hallucinate", providing incorrect yet believable answers. Fine-tuning can help but it is expensive and not ideal for retraining again and again on new data. The Retrieval-Augmented Generation (RAG) framework addresses this issue by using external documents to improve the LLM's responses through in-context learning. RAG ensures that the information provided by the LLM is not only contextually relevant but also accurate and up-to-date.

![final diagram](https://github.com/user-attachments/assets/508b3a87-ac46-4bf7-b849-145c5465a6c0)

There are four main components in RAG:

1. **Indexing:** First, documents (in any format) are split into chunks, and embeddings for these chunks are created. These embeddings are then added to a vector store.
2. **Retriever:** Then, the retriever finds the most relevant documents based on the user's query, using techniques like vector similarity from the vector store.
3. **Augment:** After that, the Augment part combines the user's query with the retrieved context into a prompt, ensuring the LLM has the information needed to generate accurate responses.
4. **Generate:** Finally, the combined query and prompt are passed to the model, which then generates the final response to the user's query.

These components of RAG allow the model to access up-to-date, accurate information and generate responses based on external knowledge. However, to ensure RAG systems are functioning effectively, it’s essential to evaluate their performance.

---

## 2. Advanced RAG Techniques ⚙️

Here are the details of all the Advanced RAG techniques covered in this repository.

| Technique        | Tools                                                  | Description                                                                                                      |
| ---------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Naive RAG        | LlamaIndex, Qdrant, Google Gemini                      | Combines retrieved data with LLMs for simple and effective responses.                                            |
| Hybrid RAG       | LlamaIndex, Qdrant, Google Gemini                      | Combines vector search and traditional methods like BM25 for better information retrieval.                       |
| Hyde RAG         | LlamaIndex, Qdrant, Google Gemini                      | Combines hybrid RAG and creates hypothetical document embeddings to find relevant information.                   |
| RAG fusion       | LlamaIndex, LangSmith, Qdrant, Google Gemini           | Generates sub-queries, ranks documents with Reciprocal Rank Fusion, and uses top results for accurate responses. |
| Contextual RAG   | LlamaIndex, Qdrant, Google Gemini, Anthropic           | Compresses retrieved documents to keep only relevant details for concise and accurate responses.                 |
| Unstructured RAG | LlamaIndex, Qdrant, FAISS, Google Gemini, Unstructured | Designed to handle documents that combine text, tables, and images.                                              |

---

## 3. Running Backend only (with Streamlit Separately)

If you want to run the backend only (with Streamlit separately), please follow the instructions in the `README.md` file located in the `backend` folder

For detailed instructions, see: [backend/README.md](backend/README.md)

---

## 4. Running the Entire Project with Docker and Docker Compose

### 4.1 Prerequisites

- Docker: [Install Docker](https://docs.docker.com/get-docker/)
- Docker Compose: [Install Docker Compose](https://docs.docker.com/compose/install/)

### 4.2 Steps

#### 1. Clone the Project

```bash
git clone https://github.com/buithanhdam/rag-app-agent-llm.git
cd rag-app-agent-llm
```

#### 2. Configure Environment Variables

- Create `.env` files in the `backend` and `frontend` folders (if needed) and fill in the required environment variables. For example:

```bash
cp ./frontend/.env.example ./frontend/.env
cp ./backend/.env.example ./backend/.env
```

```plaintext
# For backend .env
GOOGLE_API_KEY=<your_google_api_key>
OPENAI_API_KEY=<your_openai_api_key>
ANTHROPIC_API_KEY=<your_anthropic_api_key>
BACKEND_API_URL=http://localhost:8000
QDRANT_URL=http://localhost:6333

MYSQL_USER=your_mysql_user
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=your_mysql_host
MYSQL_PORT=your_mysql_port
MYSQL_DB=your_mysql_db
MYSQL_ROOT_PASSWORD=root_password

# For frontend .env
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
```

#### 3. Build and Run the Project

```bash
docker-compose up --build
```

This command will build and run all the services defined in `docker-compose.yml`.

#### 4. Set Up MySQL Database 

```bash
docker exec -it your-container-name mysql -u root -p 
```

- Enter `root password` (configured in `backend/.env` or `docker-compose.yml`).
- Run the following SQL queries:

  ```bash
  CREATE USER 'user'@'%' IDENTIFIED BY '1';
  GRANT ALL PRIVILEGES ON ragagent.* TO 'user'@'%';
  FLUSH PRIVILEGES;
  ```
  ```bash
  CREATE DATABASE ragagent;
  ```

#### 5. Access the Application

- **Frontend**: Open your browser and go to `http://localhost:3000`.
- **Backend**: The backend API will run on `http://localhost:8000`.
- **qdrant**: Exposes ports `6333`, `6334`.
- **mysql**: Exposes port `3306`.

#### 6. Stop the Project

To stop all services, run:

```bash
docker-compose down
```

---

## 5. Project Structure

- **backend/**: Contains the backend source code.
  - `README.md`: Instructions for running the backend with Streamlit separately.
  - `Dockerfile.backend`: Dockerfile for building the backend.
  - `requirements.txt`: Backend dependencies.

- **frontend/**: Contains the frontend source code.
  - `Dockerfile.frontend`: Dockerfile for building the frontend.
  - `next.config.js`: Next.js configuration.

- **docker-compose.yml**: Docker Compose configuration file for running the entire project.

- **Jenkinsfile**: Jenkins configuration file for CI/CD.