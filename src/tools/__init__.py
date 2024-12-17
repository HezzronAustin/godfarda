"""Tools package for the AI Tools Ecosystem.

This package contains all the tool implementations.
"""

from .text_analyzer import TextAnalyzer
from src.tools.communication.telegram.message import TelegramMessageTool
from src.tools.ai.ollama.chat import OllamaChatTool

# Make tools available for import
__all__ = ['TextAnalyzer', 'TelegramMessageTool', 'OllamaChatTool']

def register_tools():
    """Register all available tools."""
    from ..core.registry import registry
    registry.register_tool(TextAnalyzer)
    registry.register_tool(TelegramMessageTool)
    registry.register_tool(OllamaChatTool)
