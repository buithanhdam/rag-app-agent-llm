# agent-llm-rag-app-backend

## Backend Structure

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
- `api/`: Contains backend API logic for FastAPI.
- `data/`: Directory for data storage, including Qdrant storage.
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
   git clone https://github.com/buithanhdam/rag-app-agent-llm.git
   cd rag-app-agent-llm
   cd backend
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
- FastAPI service uses `./Dockerfile.backend`.
- Streamlit service uses `./Dockerfile.streamlit`.

---

## Troubleshooting
- Ensure `.env` is correctly configured.
- Run `docker-compose up --build` if there are changes in the Docker configuration.
- Verify that all required ports are available (8000, 8501, 6333).

---

This documentation provides all necessary steps to set up, run, and manage the project efficiently.

