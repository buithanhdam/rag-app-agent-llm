# Agent LLM RAG App Backend

## Table of Contents

1. [Backend Structure](#1-backend-structure)
2. [Installation and Setup](#2-installation-and-setup)
3. [Environment Variables Setup](#3-environment-variables-setup)
4. [Running the Application](#4-running-the-application)
5. [Using Docker](#5-using-docker)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Backend Structure

```
.
├── __pycache__
├── .theflow
├── api
├── data
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

- `api/`: Contains API logic for FastAPI.
- `data/`: Stores data, including Qdrant storage.
- `logs/`: Stores log files.
- `src/`: Additional source code.
- `venv/`: Virtual environment containing dependencies.
- `.env`: Environment variables file.
- `.gitignore`: Lists files and directories to ignore in Git.
- `app_fastapi.py`: Main FastAPI application.
- `app_streamlit.py`: Main Streamlit application.
- `docker-compose.yaml`: Docker Compose configuration.
- `requirements.txt`: Backend dependencies.
- `requirements_streamlit.txt`: Streamlit frontend dependencies.

---

## 2. Installation and Setup

### 2.1. Prerequisites

- Install [Docker](https://docs.docker.com/get-docker/).
- Install [Git](https://git-scm.com/downloads).
- Use Python 3.9+.

### 2.2. Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/buithanhdam/rag-app-agent-llm.git
   cd rag-app-agent-llm/backend
   ```

2. **Set up the virtual environment**

   - **Unix/macOS:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - **Windows:**
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

## 3. Environment Variables Setup

1. **Copy `.env.example` to `.env`**

   ```bash
   cp .env.example .env
   ```

2. **Configure the environment variables**

   ```plaintext
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

   AWS_ACCESS_KEY_ID=
   AWS_SECRET_ACCESS_KEY=
   AWS_REGION_NAME=
   AWS_STORAGE_TYPE=
   AWS_ENDPOINT_URL=
   ```

---

## 4. Running the Application

### 4.1. Run FastAPI Backend

```bash
uvicorn app_fastapi:app --host 0.0.0.0 --port 8000 --reload
```

- Access API at: `http://127.0.0.1:8000`

### 4.2. Run Streamlit Frontend

```bash
streamlit run app_streamlit.py --server.port=8501 --server.address=0.0.0.0
```

- Access UI at: `http://localhost:8501`

---

## 5. Using Docker

### 5.1. Build and Run Services

1. Ensure Docker is running.
2. Build and start containers:

   ```bash
   docker-compose build
   docker-compose up
   ```

### 5.2. Included Services

- **fastapi**: Exposes port `8000`.
- **streamlit**: Exposes port `8501`.
- **qdrant**: Exposes ports `6333`, `6334`.
- **mysql**: Exposes port `3306`.

### 5.3. Set Up MySQL Database

```bash
docker exec -it your-container-name mysql -u root -p 
```

- Enter `root password` (configured in `.env` or `docker-compose.yml`).
- Run the following SQL queries:

  ```bash
  CREATE USER 'user'@'%' IDENTIFIED BY '1';
  GRANT ALL PRIVILEGES ON ragagent.* TO 'user'@'%';
  FLUSH PRIVILEGES;
  ```
  ```bash
  CREATE DATABASE ragagent;
  ```

### 5.4. Accessing Services

- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

### 5.5. Stopping Services

```bash
docker-compose down
```

### 5.6. Additional Docker Information

- Docker network: `rag-app-network` (bridge).
- FastAPI service uses `./Dockerfile.backend`.
- Streamlit service uses `./Dockerfile.streamlit`.

---

## 6. Troubleshooting

- Ensure `.env` is correctly configured.
- If there are changes in Docker, run:
  ```bash
  docker-compose up --build
  ```
- Verify that required ports (8000, 8501, 6333) are not in use.

---

This documentation provides all necessary steps to set up, run, and manage the project efficiently.