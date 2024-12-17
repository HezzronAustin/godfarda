"""
Base AI Model Interface

This module defines the base interface for AI model implementations,
allowing for easy swapping between different AI providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class MessageRole(Enum):
    """Standard message roles across different AI providers"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"

@dataclass
class Message:
    """Standardized message format for AI interactions"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    
@dataclass
class ModelResponse:
    """Standardized response format from AI models"""
    content: str
    model: str
    usage: Dict[str, int]
    raw_response: Dict[str, Any]

class AIModel(ABC):
    """Abstract base class for AI model implementations"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the model and any necessary resources"""
        pass
    
    @abstractmethod
    async def chat(self, 
                  messages: List[Message], 
                  temperature: float = 0.7,
                  max_tokens: Optional[int] = None,
                  **kwargs) -> ModelResponse:
        """
        Send a chat request to the AI model
        
        Args:
            messages: List of messages in the conversation
            temperature: Controls randomness in responses (0.0 to 1.0)
            max_tokens: Maximum tokens in the response
            **kwargs: Additional model-specific parameters
            
        Returns:
            ModelResponse object containing the model's response
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup any resources used by the model"""
        pass

class AIModelFactory:
    """Factory class for creating AI model instances"""
    
    _models: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, model_class: type) -> None:
        """Register a new AI model implementation"""
        if not issubclass(model_class, AIModel):
            raise ValueError(f"Model class must inherit from AIModel: {model_class}")
        cls._models[name.lower()] = model_class
    
    @classmethod
    def create(cls, name: str, **kwargs) -> AIModel:
        """Create an instance of the specified AI model"""
        model_class = cls._models.get(name.lower())
        if not model_class:
            raise ValueError(f"Unknown model type: {name}. Available models: {list(cls._models.keys())}")
        return model_class(**kwargs)
    
    @classmethod
    def available_models(cls) -> List[str]:
        """Get list of available model implementations"""
        return list(cls._models.keys())
