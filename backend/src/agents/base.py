from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from src.agents.llm import BaseLLM
from llama_index.core.llms import ChatMessage
# Base Types and Data Classes
class AgentType(Enum):
    DEFAULT = "DEFAULT"
    CODING = "CODING"
    PLANNING = "PLANNING"
    REFLECTION = "REFLECTION"

@dataclass
class AgentProcessingResult:
    user_input: str
    agent_id: str
    agent_name: str
    user_id: str
    session_id: str
    additional_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResponse:
    metadata: AgentProcessingResult
    output: Union[Any, str]
    streaming: bool
    
class AgentCallbacks:
    def on_llm_new_token(self, token: str) -> None:
        pass
    
    def on_agent_start(self, agent_name: str) -> None:
        pass
    
    def on_agent_end(self, agent_name: str) -> None:
        pass

@dataclass
class AgentOptions:
    name: str
    description: str
    id: Optional[str] = None
    region: Optional[str] = None
    save_chat: bool = True
    callbacks: Optional[AgentCallbacks] = None
    
@dataclass
class Message:
    role: str
    content: List[Dict[str, str]]
    timestamp: datetime = field(default_factory=datetime.datetime.now)
    
class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, llm: BaseLLM, options: AgentOptions):
        self.llm = llm
        self.name = options.name
        self.description = options.description
        self.id = options.id
        self.region = options.region
        self.save_chat = options.save_chat
        self.callbacks = options.callbacks or AgentCallbacks()
    @staticmethod
    def generate_key_from_name(name: str) -> str:
        import re
        # Remove special characters and replace spaces with hyphens
        key = re.sub(r'[^a-zA-Z\s-]', '', name)
        key = re.sub(r'\s+', '-', key)
        return key.lower()
    def _create_system_message(self, prompt: str) -> ChatMessage:
        """Create a system message with the given prompt"""
        return ChatMessage(role="system", content=prompt)
    
    @abstractmethod
    async def run(self,query: str,verbose: bool = False,chat_history: List[ChatMessage] = [], *args, **kwargs) -> Any:
        """Main execution method that must be implemented by all agents"""
        pass
    def is_streaming_enabled(self) -> bool:
        return False
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass