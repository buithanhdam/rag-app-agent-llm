from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.db.models import Agent, LLMConfig, LLMFoundation, AgentLLM, AgentConfig
from api.schemas.agent import (
    AgentCreate, AgentUpdate, AgentResponse,
)
from src.agents import ReActAgent, AgentOptions
from src.agents.llm import GeminiLLM  # Import other LLM providers as needed

class AgentService:
    @staticmethod
    async def create_agent(db: Session, agent_create: AgentCreate) -> Agent:
        agent = Agent(**agent_create.dict())
        db.add(agent)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    async def get_agent(db: Session, agent_id: int) -> Optional[Agent]:
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent

    @staticmethod
    async def get_all_agents(db: Session, skip: int = 0, limit: int = 100) -> List[Agent]:
        return db.query(Agent).offset(skip).limit(limit).all()

    @staticmethod
    async def update_agent(db: Session, agent_id: int, agent_update: AgentUpdate) -> Agent:
        agent = await AgentService.get_agent(db, agent_id)
        update_data = agent_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(agent, field, value)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    async def delete_agent(db: Session, agent_id: int) -> bool:
        agent = await AgentService.get_agent(db, agent_id)
        db.delete(agent)
        db.commit()
        return True

    @staticmethod
    async def link_llm_config(db: Session, agent_id: int, llm_config_id: int) -> AgentConfig:
        agent_config = AgentConfig(agent_id=agent_id, config_id=llm_config_id)
        db.add(agent_config)
        db.commit()
        db.refresh(agent_config)
        return agent_config

    @staticmethod
    async def unlink_llm_config(db: Session, agent_id: int, llm_config_id: int) -> bool:
        agent_config = db.query(AgentConfig).filter(
            AgentConfig.agent_id == agent_id,
            AgentConfig.config_id == llm_config_id
        ).first()
        if not agent_config:
            raise HTTPException(status_code=404, detail="LLM config not linked to agent")
        db.delete(agent_config)
        db.commit()
        return True