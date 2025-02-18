# Rag Application with Multi-Agent Orchestrator

This repository is an advanced implementation of the Retrieval-Augmented Generation (RAG) framework combined with multi-agent orchestration techniques. It integrates various agentic patterns such as **Planning (ReAct flow)**, **Reflection**, and **Multi-Agent** workflows to enhance response generation and contextual understanding.

## Table of Contents

1. [Introduction to RAG](#1-introduction-to-rag)
2. [Multi Agent Orchestrator](#2-multi-agent-orchestrator)
3. [Advanced RAG Techniques](#3-advanced-rag-techniques)
4. [Running Backend with Streamlit Separately](#4-running-backend-with-streamlit-separately)
5. [Running the Entire Project with Docker and Docker Compose](#5-running-the-entire-project-with-docker-and-docker-compose)
6. [Project Structure](#6-project-structure)
7. [Contributing](#7-contributing)
8. [License](#8-license)
9. [References](#9-references)

---

## 1. Introduction to RAG 💡

Large Language Models are trained on a fixed dataset, which limits their ability to handle private or recent information. They can sometimes "hallucinate," providing incorrect yet believable answers. Fine-tuning can help, but it is expensive and not ideal for frequent updates. The Retrieval-Augmented Generation (RAG) framework addresses this issue by using external documents to improve the LLM's responses through in-context learning. RAG ensures that the information provided by the LLM is not only contextually relevant but also accurate and up-to-date.

![final diagram](https://github.com/user-attachments/assets/508b3a87-ac46-4bf7-b849-145c5465a6c0)

There are four main components in RAG:

1. **Indexing:** Documents are split into chunks, and embeddings for these chunks are created and stored in a vector database.
2. **Retriever:** The retriever finds the most relevant documents based on the user's query using vector similarity search.
3. **Augment:** The retrieved documents are combined with the user query to form a prompt that provides contextual information.
4. **Generate:** The prompt is fed into the LLM to generate an accurate and context-aware response.

---

## 2. Multi Agent Orchestrator

This repository implements multi-agent workflows that enhance LLM capabilities through agent collaboration. It integrates:

- **ReAct Flow** for planning and execution
- **Reflection Mechanisms** to improve agent performance
- **Multi-Agent Coordination** for complex problem-solving

### How It Works

1. User input is classified to determine the appropriate agent.
2. The orchestrator selects the best agent based on historical context and agent capabilities.
3. The selected agent processes the input and generates a response.
4. The orchestrator updates conversation history and returns the response to the user.

For further exploration:

- [Agentic Patterns Repo](https://github.com/neural-maze/agentic_patterns/)
- [Multi-Agent Orchestrator](https://github.com/awslabs/multi-agent-orchestrator)

![Multi-Agent Workflow](https://raw.githubusercontent.com/awslabs/multi-agent-orchestrator/main/img/flow.jpg)

---

## 3. Advanced RAG Techniques ⚙️

This repository supports several advanced RAG techniques:

| Technique        | Tools                                                  | Description                                                                                                      |
| ---------------- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Naive RAG        | LlamaIndex, Qdrant, Google Gemini                      | Basic retrieval-based response generation.                                                                      |
| Hybrid RAG       | LlamaIndex, Qdrant, Google Gemini                      | Combines vector search with traditional methods like BM25.                                                      |
| Hyde RAG         | LlamaIndex, Qdrant, Google Gemini                      | Uses hypothetical document embeddings to improve retrieval accuracy.                                            |
| RAG Fusion       | LlamaIndex, LangSmith, Qdrant, Google Gemini           | Generates sub-queries, ranks results with Reciprocal Rank Fusion, and improves retrieval performance.          |
| Contextual RAG   | LlamaIndex, Qdrant, Google Gemini, Anthropic           | Compresses retrieved documents to keep only the most relevant details.                                         |
| Unstructured RAG | LlamaIndex, Qdrant, FAISS, Google Gemini, Unstructured | Handles text, tables, and images for more diverse content retrieval.                                            |

---

## 4. Running Backend Only (With Streamlit Separately)

To run the backend separately with Streamlit, follow the instructions in the [backend README](backend/README.md).

---

## 5. Running the Entire Project with Docker and Docker Compose

### 5.1 Prerequisites

- [Install Docker](https://docs.docker.com/get-docker/)
- [Install Docker Compose](https://docs.docker.com/compose/install/)

### 5.2 Steps

#### 1. Clone the Project

```bash
git clone https://github.com/buithanhdam/rag-app-agent-llm.git
cd rag-app-agent-llm
```

#### 2. Configure Environment Variables

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

#### 4. Set Up MySQL Database

```bash
docker exec -it your-container-name mysql -u root -p
```
- Enter `root password` (configured in `.env` or `docker-compose.yml`).

Run SQL queries:

```sql
CREATE USER 'user'@'%' IDENTIFIED BY '1';
GRANT ALL PRIVILEGES ON ragagent.* TO 'user'@'%';
FLUSH PRIVILEGES;
CREATE DATABASE ragagent;
```

#### 5. Access the Application

- **Frontend**: `http://localhost:3000`
- **Backend**: `http://localhost:8000`
- **Qdrant**: Exposes ports `6333`, `6334`
- **MySQL**: Exposes port `3306`

#### 6. Stop the Project

```bash
docker-compose down
```

---

## 6. Project Structure

- **backend/**: Backend source code
  - `Dockerfile.backend`: Backend container setup
  - `requirements.txt`: Backend dependencies

- **frontend/**: Frontend source code
  - `Dockerfile.frontend`: Frontend container setup
  - `next.config.js`: Next.js configuration

- **docker-compose.yml**: Docker Compose setup
- **Jenkinsfile**: CI/CD configuration

---

## 7. Contributing

Contributions are welcome! Please submit an issue or a pull request to improve this project.

---

## 8. License

This project is licensed under the MIT License.

---

## 9. References

- [Agentic Patterns Repo](https://github.com/neural-maze/agentic_patterns/)
- [Multi-Agent Orchestrator](https://github.com/awslabs/multi-agent-orchestrator)
- [kotaemon](https://github.com/Cinnamon/kotaemon)
- [multi-agent](https://github.com/buithanhdam/multi-agent)
- [RAG Cookbook](https://github.com/athina-ai/rag-cookbook)

