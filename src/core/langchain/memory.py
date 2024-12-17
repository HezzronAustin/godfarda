"""
LangChain Memory Integration

This module provides memory management for LangChain agents using simple conversation buffer.
"""

from typing import Any, Dict, List
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
import logging

logger = logging.getLogger(__name__)

class GodFardaMemory(ConversationBufferMemory):
    """Custom memory implementation for GodFarda using conversation buffer."""
    
    def __init__(self):
        """Initialize the memory with conversation buffer."""
        super().__init__(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        self._user_info: Dict[str, Any] = {}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save context from this conversation to buffer.
        
        Args:
            inputs: Input dictionary containing user message and info
            outputs: Output dictionary containing assistant's response
        """
        # Extract user info if provided
        if "user_info" in inputs:
            self._user_info.update(inputs["user_info"])
            # Remove user_info from inputs to avoid storing it in chat history
            inputs = {k: v for k, v in inputs.items() if k != "user_info"}
        
        super().save_context(inputs, outputs)
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables for the conversation.
        
        Args:
            inputs: Input dictionary
            
        Returns:
            Dictionary containing chat history
        """
        memory_vars = super().load_memory_variables(inputs)
        
        # Add user info to memory variables if available
        if self._user_info:
            memory_vars["user_info"] = self._user_info
            
        return memory_vars
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get stored user information.
        
        Returns:
            Dictionary containing user information
        """
        return self._user_info.copy()
    
    def clear(self) -> None:
        """Clear memory contents."""
        super().clear()
        self._user_info.clear()
