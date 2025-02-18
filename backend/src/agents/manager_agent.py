from typing import Any, Dict, List, Optional, Tuple
from llama_index.core.llms import ChatMessage
from src.agents.llm import BaseLLM
import logging
import json
from colorama import Fore
from src.agents.base import BaseAgent, AgentOptions
from src.agents.utils import clean_json_response
logger = logging.getLogger(__name__)

CLASSIFY_PROMPT = """\
You are AgentMatcher, an intelligent assistant designed to analyze user queries and match them with 
the most suitable agent or department. Your task is to understand the user request,
identify key entities and intents, and determine which agent or department would be best equipped
to handle the query.

Important: The user input may be a follow-up response to a previous interaction.
The conversation history, including the name of the previously selected agent, is provided.
If the user's input appears to be a continuation of the previous conversation
(e.g., 'yes', 'ok', 'I want to know more', '1'), select the same agent as before.

Available agents and their capabilities: {agent_descriptions}

Based on the user input and chat history, determine the most appropriate agent and provide a confidence score (0-1).

Respond in JSON format:
{{
    "selected_agent": "agent_id",
    "confidence": 0.0,
    "reasoning": "brief explanation"
}}
        
User input: {user_input}
Recent chat history: {chat_history}
\
"""

class ManagerAgent(BaseAgent):
    def __init__(self, llm: BaseLLM, options: AgentOptions):
        super().__init__(llm, options)
        self.agent_registry: Dict[str, BaseAgent] = {}
    def register_agent(self, agent: BaseAgent) -> None:
        """Register a new agent with the manager"""
        self.agent_registry[agent.id] = agent
        logger.info(f"{Fore.CYAN}Registered agent: {agent.id} ({agent.name})")

    def _get_agent_descriptions(self) -> str:
        """Generate formatted descriptions of all registered agents"""
        descriptions = []
        for agent_id, agent in self.agent_registry.items():
            descriptions.append(f"- {agent.name} (ID: {agent_id}): {agent.description}")
        return "\n".join(descriptions)

    def _format_chat_history(self, chat_history: List[ChatMessage]) -> str:
        """Format recent chat history for context"""
        if not chat_history:
            return "No recent chat history"
        
        # Take last 3 messages for context
        formatted = []
        for msg in chat_history:
            formatted.append(f"{msg.role}: {msg.content}")
        return "\n".join(formatted)

    async def classify_request(
        self,
        user_input: str,
        chat_history: List[ChatMessage]
    ) -> Tuple[Optional[BaseAgent], float]:
        """Classify user request using LLM and return appropriate agent with confidence score"""
        try:
            # Prepare classification prompt
            classification_prompt = CLASSIFY_PROMPT.format(
                agent_descriptions=self._get_agent_descriptions(),
                user_input=user_input,
                chat_history=self._format_chat_history(chat_history)
            )
            print(classification_prompt)
            # Get classification from LLM
            response = await self.llm.achat(classification_prompt)
            response = clean_json_response(response)
            try:
                # Parse LLM response
                classification = json.loads(response)
                selected_agent_id = classification["selected_agent"]
                confidence = float(classification["confidence"])
                reasoning = classification["reasoning"]
                
                # Get selected agent
                selected_agent = self.agent_registry.get(selected_agent_id)
                
                if selected_agent:
                    logger.info(
                        f"{Fore.CYAN}Request classified to {selected_agent.name} "
                        f"(confidence: {confidence:.2f}). Reasoning: {reasoning}{Fore.RESET}"
                    )
                    return selected_agent, confidence
                else:
                    logger.warning(f"{Fore.YELLOW}Selected agent {selected_agent_id} not found in registry")
                    return self.agent_registry.get("default"), 0.5
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"{Fore.RED}Error parsing LLM classification response: {str(e)}")
                return self.agent_registry.get("default"), 0.5
                
        except Exception as e:
            logger.error(f"{Fore.RED}Error during request classification: {str(e)}")
            return self.agent_registry.get("default"), 0.5

    async def run(
        self,
        query: str,
        user_id: str = "",
        session_id: str = "",
        chat_history: List[ChatMessage] = [],
        verbose: bool = False,
        additional_params: Dict[str, Any] = {}
    ) -> str:
        """Process user request by classifying and delegating to appropriate agent"""
        try:
            # Classify the request
            selected_agent, confidence = await self.classify_request(query, chat_history)
            
            if not selected_agent:
                response = await self.llm.achat("Answer this question: "+query,chat_history=chat_history)
                print("I'm sorry, I couldn't find an appropriate agent to handle your request.")
                return response
            
            # If confidence is too low, maybe ask for clarification
            if confidence < 0.6:
                print(
                    f"I'm not entirely sure I understand your request. "
                    f"I think {selected_agent.name} might be able to help, "
                    f"but could you please provide more details about what you need?"
                )
                response = await self.llm.achat("Answer this question: "+query,chat_history=chat_history)
                return response
            
            # Log the classification
            if verbose:
                logger.info(
                    f"{Fore.CYAN}Request classified to {selected_agent.name} "
                    f"with confidence {confidence:.2f}{Fore.RESET}"
                )
            
            # Execute the request with the selected agent
            response = await selected_agent.run(
                query=query,
                verbose = True,
                # user_id=user_id,
                # session_id=session_id,
                # chat_history=chat_history,
                # additional_params=additional_params
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return (
                "I encountered an error while processing your request. "
                "Please try again or rephrase your question."
            )

    async def get_agent_status(self) -> Dict[str, Any]:
        """Get status information about all registered agents"""
        return {
            "total_agents": len(self.agent_registry),
            "registered_agents": [
                {
                    "id": agent_id,
                    "name": agent.name,
                    "description": agent.description,
                    "status": "active"  # Could be expanded to check actual agent status
                }
                for agent_id, agent in self.agent_registry.items()
            ]
        }