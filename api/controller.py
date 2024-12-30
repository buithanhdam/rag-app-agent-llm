from fastapi import APIRouter, Request, HTTPException, Depends
from .service import AssistantService
from datetime import time
from api.auth_bearer import JWTBearer
from api.auth import sign_jwt
router = APIRouter()
global assistant
assistant = AssistantService()
# --- API Endpoints ---
# @router.post("/complete",dependencies=[Depends(JWTBearer())], tags=["complete"])
@router.post("/complete", tags=["complete"])
async def complete_text(request: Request):
    global assistant
    data = await request.json()
    message = data.get("message")
    response = assistant.predict(message)
    return response

    