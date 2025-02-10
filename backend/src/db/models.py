# src/database/models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum, Boolean, Float, create_engine
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum
from src.config import Settings

settings = Settings()
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

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    foundation_id = Column(Integer, ForeignKey("llm_foundations.id"))
    config_id = Column(Integer, ForeignKey("llm_configs.id"))
    name = Column(String(100))
    agent_type = Column(Enum(AgentType))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    configuration = Column(JSON)  # Agent-specific configuration
    tools = Column(JSON)  # Available tools for this agent
    
    # Relationships
    llm_foundations = relationship("LLMFoundation", back_populates="agents")
    llm_configs = relationship("LLMConfig", back_populates="agents")
    conversations = relationship("Conversation", secondary="agent_conversations", back_populates="agents")

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
    llm_configs = relationship("LLMConfig", back_populates="llm_foundations")
    agents = relationship("Agent", back_populates="llm_foundations")

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
    llm_foundations = relationship("LLMFoundation", back_populates="llm_configs")
    agents = relationship("Agent", back_populates="llm_configs")

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
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class AgentConversation(Base):
    __tablename__ = "agent_conversations"
    
    agent_id = Column(Integer, ForeignKey("agents.id"), primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(engine)