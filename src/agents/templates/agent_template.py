from typing import Dict, List, Any
from abc import ABC, abstractmethod
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """Configuration model for agents"""
    name: str
    allowed_tools: List[str]
    parameters: Dict[str, Any] = {}

class BaseAgent(ABC):
    """Base class for all AI agents in the ecosystem"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.tools: Dict[str, Any] = {}  # Will store tool instances
        
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the agent and load required tools
        
        Returns:
            bool: True if initialization was successful
        """
        pass
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data and return results
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            Dict containing processing results
        """
        pass
    
    async def use_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Execute a tool if the agent has permission
        
        Args:
            tool_name: Name of the tool to execute
            params: Parameters for the tool
            
        Returns:
            Tool execution results
        """
        if tool_name not in self.config.allowed_tools:
            raise PermissionError(f"Agent {self.config.name} is not allowed to use {tool_name}")
        
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} is not loaded")
            
        return await self.tools[tool_name].execute(params)
