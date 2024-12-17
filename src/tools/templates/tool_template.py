from typing import Any, Dict, Optional
from pydantic import BaseModel
from abc import ABC, abstractmethod

class ToolResponse(BaseModel):
    """Base model for tool response data"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None

class BaseTool(ABC):
    """Base class for all tools in the ecosystem"""
    
    def __init__(self):
        self.name: str = self.__class__.__name__
        self.description: str = self.__doc__ or "No description provided"
        
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        """
        Execute the tool's main functionality
        
        Args:
            params: Dictionary of parameters required by the tool
            
        Returns:
            ToolResponse: Standardized response containing execution results
        """
        pass
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema for the tool's parameters
        
        Returns:
            Dict containing the parameter schema
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate the provided parameters against the tool's schema
        
        Args:
            params: Parameters to validate
            
        Returns:
            bool: True if parameters are valid
        """
        # Implement validation logic
        return True
