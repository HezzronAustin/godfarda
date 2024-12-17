"""Base classes for agent implementations."""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

class AgentConfig(Dict[str, Any]):
    """Configuration for an agent."""
    pass

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration."""
        self.config = config
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the agent. Returns True if successful."""
        pass
    
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process input data and return results."""
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up any resources used by the agent."""
        pass
