"""Tool and Agent Registry for the AI Tools Ecosystem."""

from typing import Dict, Type, Optional
from .utils import ToolException
from ..tools.templates.tool_template import BaseTool
from ..agents.templates.agent_template import BaseAgent

class Registry:
    """Registry for managing tool and agent registration."""
    
    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._agents: Dict[str, Type[BaseAgent]] = {}
    
    def register_tool(self, tool_class: Type[BaseTool]) -> None:
        """
        Register a new tool.
        
        Args:
            tool_class: Tool class to register
            
        Raises:
            ToolException: If tool is already registered
        """
        tool_name = tool_class.__name__
        if tool_name in self._tools:
            raise ToolException(
                f"Tool {tool_name} is already registered",
                tool_name=tool_name
            )
        self._tools[tool_name] = tool_class
    
    def register_agent(self, agent_class: Type[BaseAgent]) -> None:
        """
        Register a new agent.
        
        Args:
            agent_class: Agent class to register
            
        Raises:
            ToolException: If agent is already registered
        """
        agent_name = agent_class.__name__
        if agent_name in self._agents:
            raise ToolException(
                f"Agent {agent_name} is already registered",
                tool_name=agent_name
            )
        self._agents[agent_name] = agent_class
    
    def get_tool(self, tool_name: str) -> Optional[Type[BaseTool]]:
        """Get tool class by name."""
        return self._tools.get(tool_name)
    
    def get_agent(self, agent_name: str) -> Optional[Type[BaseAgent]]:
        """Get agent class by name."""
        return self._agents.get(agent_name)
    
    def list_tools(self) -> Dict[str, str]:
        """
        List all registered tools and their descriptions.
        
        Returns:
            Dict mapping tool names to their descriptions
        """
        return {
            name: tool.__doc__ or "No description available"
            for name, tool in self._tools.items()
        }
    
    def list_agents(self) -> Dict[str, str]:
        """
        List all registered agents and their descriptions.
        
        Returns:
            Dict mapping agent names to their descriptions
        """
        return {
            name: agent.__doc__ or "No description available"
            for name, agent in self._agents.items()
        }

# Global registry instance
registry = Registry()
