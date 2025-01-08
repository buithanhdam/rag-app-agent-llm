from typing import Any, List, Optional
from llama_index.core.llms import ChatMessage

class ChatHistory:
    def __init__(self, initial_messages: List[ChatMessage], max_length: int):
        self.messages = initial_messages
        self.max_length = max_length

    def add(self, role: str, content: str):
        self.messages.append(ChatMessage(role=role, content=content))
        if len(self.messages) > self.max_length:
            self.messages = [self.messages[0]] + self.messages[-(self.max_length-1):]

    def get_messages(self) -> List[ChatMessage]:
        return self.messages
    
class PlanStep:
    def __init__(self, description: str, requires_tool: bool = False, tool_name: str = None):
        self.description = description
        self.requires_tool = requires_tool
        self.tool_name = tool_name
        self.completed = False
        self.result = None

class ExecutionPlan:
    def __init__(self):
        self.steps: List[PlanStep] = []
        self.current_step = 0
        
    def add_step(self, step: PlanStep):
        self.steps.append(step)
        
    def get_current_step(self) -> Optional[PlanStep]:
        if self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
        
    def mark_current_complete(self, result: Any = None):
        if self.current_step < len(self.steps):
            self.steps[self.current_step].completed = True
            self.steps[self.current_step].result = result
            self.current_step += 1
            
    def is_complete(self) -> bool:
        return self.current_step >= len(self.steps)
    
    def get_progress(self) -> str:
        completed = sum(1 for step in self.steps if step.completed)
        return f"Progress: {completed}/{len(self.steps)} steps completed"

def clean_json_response(response: str) -> str:
    """Clean and extract JSON from LLM response"""
    # Remove any markdown code block markers
    response = response.replace("```json", "").replace("```", "").strip()
        
    # Find the first '{' and last '}'
    start = response.find('{')
    end = response.rfind('}')
        
    if start == -1 or end == -1:
        raise ValueError("No valid JSON object found in response")
            
    # Extract just the JSON object
    return response[start:end + 1]