"""Tools package initialization."""

from typing import Dict, Any
from .text_analyzer import TextAnalyzer
from .communication.telegram.message import TelegramMessageTool
from .ai.ollama.chat import OllamaChatTool

# Make tools available for import
__all__ = ['TextAnalyzer', 'TelegramMessageTool', 'OllamaChatTool']

def register_tools():
    """Register all available tools."""
    from ..core.registry import registry
    
    # Register tools
    registry.register_tool(TextAnalyzer)
    registry.register_tool(TelegramMessageTool)
    registry.register_tool(OllamaChatTool)
