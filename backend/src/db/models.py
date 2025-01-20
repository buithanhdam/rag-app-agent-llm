# src/database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Boolean, Float
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from typing import List
from datetime import datetime

Base = declarative_base()

class RoleType(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class AgentType(enum.Enum):
    REACT = "react"
    REFLECTION = "reflection"
    # Add more agent types as needed

class LLMProvider(enum.Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"

class LLMFoundation(Base):
    __tablename__ = "llm_foundations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(Enum(LLMProvider), nullable=False)
    model_name = Column(String(100), nullable=False)
    model_id = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    capabilities = Column(JSON)  # Store model capabilities
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    configs = relationship("LLMConfig", back_populates="foundation")
    agents = relationship("Agent", secondary="agent_llm", back_populates="llm_foundations")

class LLMConfig(Base):
    __tablename__ = "llm_configs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    foundation_id = Column(Integer, ForeignKey("llm_foundations.id"))
    name = Column(String(100))
    temperature = Column(Float)
    max_tokens = Column(Integer)
    top_p = Column(Float, nullable=True)
    frequency_penalty = Column(Float, nullable=True)
    presence_penalty = Column(Float, nullable=True)
    system_prompt = Column(Text)
    stop_sequences = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    foundation = relationship("LLMFoundation", back_populates="configs")
    agents = relationship("Agent", secondary="agent_config", back_populates="llm_configs")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100))
    agent_type = Column(Enum(AgentType))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    configuration = Column(JSON)  # Agent-specific configuration
    tools = Column(JSON)  # Available tools for this agent
    
    # Relationships
    llm_foundations = relationship("LLMFoundation", secondary="agent_llm", back_populates="agents")
    llm_configs = relationship("LLMConfig", secondary="agent_config", back_populates="agents")
    conversations = relationship("Conversation", secondary="agent_conversations", back_populates="agents")

class AgentLLM(Base):
    __tablename__ = "agent_llm"
    
    agent_id = Column(Integer, ForeignKey("agents.id"), primary_key=True)
    foundation_id = Column(Integer, ForeignKey("llm_foundations.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_primary = Column(Boolean, default=False)  # Indicate if this is the primary LLM for the agent

class AgentConfig(Base):
    __tablename__ = "agent_config"
    
    agent_id = Column(Integer, ForeignKey("agents.id"), primary_key=True)
    config_id = Column(Integer, ForeignKey("llm_configs.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    agents = relationship("Agent", secondary="agent_conversations", back_populates="conversations")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(Enum(RoleType))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)  # Track which agent generated the response
    llm_config_id = Column(Integer, ForeignKey("llm_configs.id"), nullable=True)  # Track which LLM config was used
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    
    agent_id = Column(Integer, ForeignKey("agents.id"), primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())