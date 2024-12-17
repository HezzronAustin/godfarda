"""Base classes and interfaces for tool implementation.

This module provides the base classes and core functionality that should be
implemented by any new tool in the AI Tools Ecosystem.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseToolTemplate(ABC):
    """Base class for tool implementation.
    
    This class defines the interface that all tools should implement.
    Inherit from this class when creating a new tool.
    
    Attributes:
        name (str): The name of the tool
        description (str): A brief description of what the tool does
        config (Dict[str, Any]): Configuration parameters for the tool
    """

    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the tool.
        
        Args:
            name: The name of the tool
            description: A brief description of what the tool does
            config: Optional configuration parameters
        """
        self.name = name
        self.description = description
        self.config = config or {}

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize any necessary resources for the tool.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool's main functionality.
        
        Args:
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool
            
        Returns:
            Any: The result of the tool execution
            
        Raises:
            NotImplementedError: If the method is not implemented
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up any resources used by the tool."""
        pass

    def validate_config(self) -> bool:
        """Validate the tool's configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return True

    def __str__(self) -> str:
        """Return a string representation of the tool.
        
        Returns:
            str: A string representation of the tool
        """
        return f"{self.name}: {self.description}"
