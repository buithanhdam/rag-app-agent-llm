from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.db.mysql import get_db
from api.services.agent import AgentService
from api.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse
)
from api.schemas.llm import LLMConfigResponse

agent_router = APIRouter(prefix="/agent", tags=["agent"])

@agent_router.post("/create", response_model=AgentResponse)
async def create_agent(agent_create: AgentCreate, db: Session = Depends(get_db)):
    return await AgentService.create_agent(db, agent_create)

@agent_router.get("/get/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int, db: Session = Depends(get_db)):
    return await AgentService.get_agent(db, agent_id)

@agent_router.get("/get-all", response_model=List[AgentResponse])
async def get_all_agents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return await AgentService.get_all_agents(db, skip, limit)

@agent_router.put("/update/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, agent_update: AgentUpdate, db: Session = Depends(get_db)):
    return await AgentService.update_agent(db, agent_id, agent_update)

@agent_router.delete("/delete/{agent_id}", response_model=bool)
async def delete_agent(agent_id: int, db: Session = Depends(get_db)):
    return await AgentService.delete_agent(db, agent_id)

@agent_router.post("/{agent_id}/link_llm_config", response_model=LLMConfigResponse)
async def link_llm_config(agent_id: int, llm_config_id: int, db: Session = Depends(get_db)):
    return await AgentService.link_llm_config(db, agent_id, llm_config_id)

@agent_router.post("/{agent_id}/unlink_llm_config", response_model=bool)
async def unlink_llm_config(agent_id: int, llm_config_id: int, db: Session = Depends(get_db)):
    return await AgentService.unlink_llm_config(db, agent_id, llm_config_id)