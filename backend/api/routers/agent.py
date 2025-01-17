from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio

from api.services.agent import AgentChat

# Create router
agent_router = APIRouter(prefix="/agent", tags=["agent"])

# Request model
class ChatRequest(BaseModel):
    query: str

# Response model
class ChatResponse(BaseModel):
    response: str

# Response model for reset endpoint
class ResetResponse(BaseModel):
    status: str
    message: str

# Initialize agent chat globally
agent_chat = AgentChat()

@agent_router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint for agent chat interaction
    
    Args:
        request (ChatRequest): Contains the user query
    
    Returns:
        ChatResponse: Agent's response to the query
    """
    try:
        # Use the existing get_response method from AgentChat
        response = await agent_chat.get_response(request.query)
        return ChatResponse(response=response)
    except Exception as e:
        # Handle any potential errors
        raise HTTPException(status_code=500, detail=str(e))

@agent_router.post("/reset", response_model=ResetResponse)
async def reset_chat_endpoint():
    """
    Endpoint to reset the chat history
    
    Returns:
        ResetResponse: Confirmation of chat history reset
    """
    try:
        # Call the reset_chat method
        agent_chat.reset_chat()
        return ResetResponse(
            status="success", 
            message="Chat history has been successfully reset"
        )
    except Exception as e:
        # Handle any potential errors
        raise HTTPException(status_code=500, detail=str(e))