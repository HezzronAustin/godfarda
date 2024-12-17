"""Agents package for the AI Tools Ecosystem."""

from .text_agent import TextAgent

# Make agents available for import
__all__ = ['TextAgent']

def register_agents():
    """Register all available agents."""
    from ..core.registry import registry
    registry.register_agent(TextAgent)
