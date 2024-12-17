"""
Agents package initialization.
Exposes various agent implementations for the AI Tools Ecosystem.
"""

from .communications.communications_agent import CommunicationsAgent
from .text_agent import TextAgent

# Make agents available for import
__all__ = ['CommunicationsAgent', 'TextAgent']

def register_agents():
    """Register all available agents."""
    from ..core.registry import registry
    registry.register_agent(TextAgent)

# Import communications_agent lazily to avoid circular imports
from .communications.communications_agent import CommunicationsAgent
