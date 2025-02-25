# tool_manager.py

from typing import Dict, List, Optional, Callable
from llama_index.core.tools import FunctionTool
import logging
from inspect import getdoc
from src.tools.testing_tool import get_weather
class ToolManager:
    """
    Manages registration and organization of tools for agents
    """
    def __init__(self):
        self.tools: Dict[str, FunctionTool] = {}
        self.logger = logging.getLogger(__name__)

    def register(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> FunctionTool:
        """
        Directly register a function as a tool
        
        Args:
            func: The function to register
            name: Optional custom name for the tool
            description: Optional description of the tool
            
        Returns:
            FunctionTool: The registered tool
        """
        tool_name = name or func.__name__
        tool_description = description or getdoc(func) or "No description provided"
        
        # Create the tool
        tool = FunctionTool.from_defaults(
            fn=func,
            name=tool_name,
            description=tool_description
        )
        
        # Store the tool
        self.tools[tool_name] = tool
        self.logger.info(f"Registered tool: {tool_name}")
        
        return tool
    
    def register_many(self, tools: Dict[str, Callable]) -> List[FunctionTool]:
        """
        Register multiple tools at once
        
        Args:
            tools: Dictionary of name: function pairs to register
            
        Returns:
            List[FunctionTool]: List of registered tools
        """
        registered_tools = []
        for name, func in tools.items():
            tool = self.register(func, name=name)
            registered_tools.append(tool)
        return registered_tools

    def get_tool(self, name: str) -> Optional[FunctionTool]:
        """Get a specific tool by name"""
        return self.tools.get(name)
    
    def get_all_tools(self) -> List[FunctionTool]:
        """Get all registered tools"""
        return list(self.tools.values())
    
    def remove_tool(self, name: str) -> bool:
        """Remove a tool by name"""
        if name in self.tools:
            del self.tools[name]
            self.logger.info(f"Removed tool: {name}")
            return True
        return False

# Create a global instance
tool_manager = ToolManager()

tool_manager.register_many({
    "get_weather": get_weather
})