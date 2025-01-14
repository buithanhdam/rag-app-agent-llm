import logging
from typing import Optional, List

from src.agents import (
    ReActAgent,
    AgentOptions,
)
# from src.tools.tool_manager import weather_tool
from src.agents.llm import GeminiLLM
from llama_index.core.llms import ChatMessage
from src.tools.tool_manager import tool_manager

class AgentChat:
    def __init__(self):
        # Initialize LLM
        self.llm = GeminiLLM()
        
        # Logging setup
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        
        self.planning_agent = ReActAgent(
            self.llm,
            AgentOptions(
                id="planning",
                name="Planning Assistant",
                description="Assists with project planning, task breakdown, and using tool"
            ),
            tools=tool_manager.get_all_tools()
        )
        
        # Chat history to provide context
        self.chat_history: List[ChatMessage] = []
    
    async def get_response(self, user_input: str, verbose: bool = True) -> str:
        """
        Process user input by routing to appropriate agent
        
        Args:
            user_input (str): User's query
            verbose (bool): Whether to log detailed information
        
        Returns:
            str: Agent's response
        """
        try:
            # Process the input and get a response
            response = await self.planning_agent.run(
                query=user_input,
                # chat_history=self.chat_history,
                verbose=verbose
            )
            
            # Update chat history
            self.chat_history.append(ChatMessage(role="user", content=user_input))
            self.chat_history.append(ChatMessage(role="assistant", content=response))
            
            # Trim chat history to last 5 messages to prevent context overflow
            self.chat_history = self.chat_history[-10:]
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error in get_response: {e}")
            return "I'm sorry, I encountered an error processing your request."
    
    def reset_chat(self):
        """Reset the chat history"""
        self.chat_history = []