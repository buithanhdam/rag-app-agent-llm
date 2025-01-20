from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.db.models import Conversation, Message, AgentConversation, Agent, LLMConfig
from api.schemas.chat import (
    ConversationCreate, ConversationUpdate, ConversationResponse,
    MessageCreate, MessageResponse
)
from src.agents import ReActAgent, AgentOptions
from src.agents.llm import GeminiLLM  # Import other LLM providers as needed
from src.tools.tool_manager import tool_manager

class ChatService:
    @staticmethod
    def create_llm_instance(llm_config: LLMConfig):
        """Create LLM instance based on provider and config"""
        provider = llm_config.foundation.provider
        if provider == "gemini":
            return GeminiLLM()
        # Add other providers as needed
        raise HTTPException(status_code=400, detail=f"Unsupported LLM provider: {provider}")

    @staticmethod
    async def setup_agent(db: Session, agent_id: int, llm_config_id: int) -> ReActAgent:
        """Setup agent with specified LLM config"""
        # Get agent and config
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
            
        llm_config = db.query(LLMConfig).filter(LLMConfig.id == llm_config_id).first()
        if not llm_config:
            raise HTTPException(status_code=404, detail="LLM config not found")

        # Create LLM instance
        llm = ChatService.create_llm_instance(llm_config)

        # Create and return agent
        return ReActAgent(
            llm=llm,
            options=AgentOptions(
                id=str(agent.id),
                name=agent.name,
                description=agent.description
            ),
            tools=tool_manager.get_all_tools()
        )

    @staticmethod
    async def create_conversation(db: Session, conv_create: ConversationCreate) -> Conversation:
        conversation = Conversation(
            title=conv_create.title
        )
        db.add(conversation)
        db.flush()

        for agent_id in conv_create.agent_ids:
            agent_conv = AgentConversation(
                agent_id=agent_id,
                conversation_id=conversation.id
            )
            db.add(agent_conv)

        try:
            db.commit()
            db.refresh(conversation)
            return conversation
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Invalid agent IDs")

    @staticmethod
    async def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
        conversation = db.query(Conversation)\
            .filter(Conversation.id == conversation_id)\
            .first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return conversation

    @staticmethod
    async def get_all_conversations(db: Session, skip: int = 0, limit: int = 100, agent_id: Optional[int] = None) -> List[Conversation]:
        query = db.query(Conversation)
        if agent_id:
            query = query.join(AgentConversation)\
                        .filter(AgentConversation.agent_id == agent_id)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def update_conversation(db: Session, conversation_id: int, conv_update: ConversationUpdate) -> Conversation:
        conversation = await ChatService.get_conversation(db, conversation_id)
        update_data = conv_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    async def delete_conversation(db: Session, conversation_id: int) -> bool:
        conversation = await ChatService.get_conversation(db, conversation_id)
        db.delete(conversation)
        db.commit()
        return True

    @staticmethod
    async def add_message(db: Session, message: MessageCreate) -> Message:
        """Add a message to the conversation, optionally using an agent to generate a response."""
        db_message = Message(**message.dict())
        db.add(db_message)
        
        # If the message is from a user and an agent is specified, generate a response
        if message.role == "user" and message.agent_id and message.llm_config_id:
            agent = await ChatService.setup_agent(db, message.agent_id, message.llm_config_id)
            response = await agent.run(
                query=message.content,
                verbose=True
            )
            
            # Add the agent's response as a new message
            agent_message = Message(
                conversation_id=message.conversation_id,
                role="assistant",
                content=response,
                agent_id=message.agent_id,
                llm_config_id=message.llm_config_id
            )
            db.add(agent_message)
        
        db.commit()
        db.refresh(db_message)
        return db_message