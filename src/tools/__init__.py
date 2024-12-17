"""
Tools Module

This module provides access to various tools used by the GodFarda system.
"""

from typing import Dict, Any, List, Type
from .templates.tool_template import BaseTool

# Dictionary to store registered tools
_tools: Dict[str, Type[BaseTool]] = {}

# Make tools available for import
__all__ = []

def register_tools():
    """Register all available tools."""
    from ..core.registry import registry
    
    # Register tools
    # registry.register_tool(TextAnalyzer)
    # registry.register_tool(TelegramMessageTool)
    # registry.register_tool(OllamaChatTool)
