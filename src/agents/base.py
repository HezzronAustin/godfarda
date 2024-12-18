from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import json

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        
    @abstractmethod
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return a response"""
        pass
        
    async def can_handle(self, messages: List[BaseMessage], conversation_id: str) -> bool:
        """Check if this agent can handle the given messages
        
        Default implementation returns True if the agent's name is mentioned
        in the last message. Override this method for more sophisticated checks.
        """
        last_message = self._extract_last_message(messages)
        if not last_message:
            return False
            
        # Simple check - see if agent name is mentioned
        return self.name.lower() in last_message.lower()
        
    def _format_chat_history(self, messages: List[BaseMessage]) -> str:
        """Format chat history into a string"""
        formatted = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
        
    def _extract_last_message(self, messages: List[BaseMessage]) -> Optional[str]:
        """Extract the last message from chat history"""
        if not messages:
            return None
        return messages[-1].content
        
    def _format_response(self, response: Any) -> Dict[str, Any]:
        """Format the response into a standardized structure"""
        if isinstance(response, dict):
            return response
        if isinstance(response, str):
            return {"response": response}
        return {"response": str(response)}
