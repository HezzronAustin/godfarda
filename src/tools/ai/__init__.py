"""
AI Tools Package

This package provides a modular interface for working with different AI models.
Currently supported models:
- Ollama (llama2, codellama, etc.)

Usage:
    from src.tools.ai import AIModel, AIModelFactory, Message, MessageRole

    # Create an Ollama model instance
    model = AIModelFactory.create("ollama", model_name="llama2")
    await model.initialize()

    # Send a chat request
    response = await model.chat([
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant"),
        Message(role=MessageRole.USER, content="Hello!")
    ])

    print(response.content)
"""

from .base import AIModel, AIModelFactory, Message, MessageRole, ModelResponse
from .ollama.model import OllamaModel

__all__ = [
    'AIModel',
    'AIModelFactory',
    'Message',
    'MessageRole',
    'ModelResponse',
    'OllamaModel',
]