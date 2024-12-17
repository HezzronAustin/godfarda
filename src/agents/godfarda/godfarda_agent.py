"""
GodFarda Agent Implementation

This module provides the GodFarda agent implementation using LangChain.
"""

from typing import Any, Dict, Optional
from src.core.langchain.agent import LangChainAgent
import logging

logger = logging.getLogger(__name__)

class GodFarda:
    """GodFarda agent implementation."""
    
    def __init__(self, model_name: str = "llama2"):
        """Initialize the GodFarda agent.
        
        Args:
            model_name: Name of the Ollama model to use
        """
        self.agent = LangChainAgent(
            model_name=model_name,
            system_message=(
                "You are GodFarda, a helpful AI assistant. "
                "You can help users with various tasks using your available tools. "
                "Always be respectful and provide clear, concise responses."
            )
        )
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message using the GodFarda agent.
        
        Args:
            data: Dictionary containing message data and user information
            
        Returns:
            Dictionary containing the agent's response
        """
        try:
            message = data.get("message", "")
            user_info = data.get("user_info", {})
            
            response = await self.agent.process_message(message, user_info)
            
            return {
                "response": response,
                "success": True
            }
            
        except Exception as e:
            error_msg = f"Error in GodFarda processing: {str(e)}"
            logger.error(error_msg)
            return {
                "error": error_msg,
                "success": False
            }
    
    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        self.agent.clear_memory()
