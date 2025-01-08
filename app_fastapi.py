from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from api.routers.agent import agent_router  # Import the router we just created

# Create FastAPI app
app = FastAPI(
    title="Multi-Agent Chat API",
    description="API for interacting with multi-agent chat system",
    version="0.1.0"
)

# Add CORS middleware to allow Streamlit to communicate with the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the agent router
app.include_router(agent_router)

# Optional: Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)