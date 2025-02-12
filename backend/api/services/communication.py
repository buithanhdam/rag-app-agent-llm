from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime

from src.db.models import (
    AgentCommunication, AgentCommunicationMember, 
    CommunicationConversation, Agent, Conversation, AgentConversation
)
from api.schemas.communication import (
    AgentCommunicationCreate, AgentCommunicationUpdate,
    AgentCommunicationMemberCreate
)

class CommunicationService:
    @staticmethod
    async def create_communication(db: Session, comm_create: AgentCommunicationCreate) -> AgentCommunication:
        try:
            communication = AgentCommunication(
                name=comm_create.name,
                description=comm_create.description,
                configuration=comm_create.configuration or {}
            )
            db.add(communication)
            db.flush()

            # Add agent members
            for agent_id in comm_create.agent_ids:
                member = AgentCommunicationMember(
                    communication_id=communication.id,
                    agent_id=agent_id,
                    role="member"
                )
                db.add(member)

            db.commit()
            db.refresh(communication)
            return communication
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid agent IDs")

    @staticmethod
    async def get_communication(db: Session, communication_id: int) -> Optional[AgentCommunication]:
        communication = db.query(AgentCommunication).filter(
            AgentCommunication.id == communication_id,
            AgentCommunication.is_active == True
        ).first()
        if not communication:
            raise HTTPException(status_code=404, detail="Communication not found")
        return communication

    @staticmethod
    async def get_all_communications(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        agent_id: Optional[int] = None
    ) -> List[AgentCommunication]:
        query = db.query(AgentCommunication)
        if agent_id:
            query = query.join(AgentCommunicationMember)\
                        .filter(AgentCommunicationMember.agent_id == agent_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def update_communication(
        db: Session,
        communication_id: int,
        comm_update: AgentCommunicationUpdate
    ) -> AgentCommunication:
        communication = await CommunicationService.get_communication(db, communication_id)
        update_data = comm_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(communication, field, value)
        db.commit()
        db.refresh(communication)
        return communication

    @staticmethod
    async def delete_communication(db: Session, communication_id: int) -> bool:
        communication = await CommunicationService.get_communication(db, communication_id)
        communication.is_active = False
        db.commit()
        return True

    @staticmethod
    async def get_communication_agents(db: Session, communication_id: int) -> List[Agent]:
        communication = await CommunicationService.get_communication(db, communication_id)
        return communication.agents