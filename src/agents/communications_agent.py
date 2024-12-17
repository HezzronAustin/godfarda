"""
Communications Agent Module

This module implements a Communications Agent that orchestrates messaging tasks across
multiple communication platforms, starting with Telegram integration.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import logging
from src.tools.communication.telegram.handler import TelegramHandler
from src.tools.ai import AIModel, AIModelFactory, Message, MessageRole, ModelResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommunicationTool(ABC):
    """Abstract base class for communication tools/handlers."""
    
    @abstractmethod
    def send_message(self, recipient: str, message: str) -> bool:
        """Send a message to a recipient."""
        pass
    
    @abstractmethod
    def receive_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a received message."""
        pass
    
    @abstractmethod
    def setup_channel(self, params: Dict[str, Any]) -> bool:
        """Set up the communication channel with given parameters."""
        pass

class TelegramToolAdapter(CommunicationTool):
    """Adapter for the existing TelegramHandler to match CommunicationTool interface."""
    
    def __init__(self):
        self.handler = TelegramHandler()
    
    def send_message(self, recipient: str, message: str) -> bool:
        try:
            # Adapt the existing TelegramHandler's methods
            return self.handler.send_message(chat_id=recipient, text=message)
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def receive_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.handler.process_update(context)
        except Exception as e:
            logger.error(f"Error processing Telegram update: {e}")
            return {}
    
    def setup_channel(self, params: Dict[str, Any]) -> bool:
        try:
            return self.handler.setup_webhook(params.get('webhook_url', ''))
        except Exception as e:
            logger.error(f"Error setting up Telegram webhook: {e}")
            return False

class CommunicationsAgent:
    """
    Main Communications Agent class that orchestrates messaging across different platforms.
    """
    
    def __init__(self, ai_model_name: str = "ollama", ai_model_params: Optional[Dict[str, Any]] = None):
        self._tools: Dict[str, CommunicationTool] = {}
        # Register the Telegram tool by default
        self.register_tool("telegram", TelegramToolAdapter())
        
        # Initialize AI model
        self.ai_model: Optional[AIModel] = None
        self.ai_model_name = ai_model_name
        self.ai_model_params = ai_model_params or {}
        
        # Conversation history for AI context
        self.conversation_history: Dict[str, List[Message]] = {}
    
    async def initialize(self) -> bool:
        """Initialize the agent and its AI model."""
        try:
            self.ai_model = AIModelFactory.create(self.ai_model_name, **self.ai_model_params)
            return await self.ai_model.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize AI model: {e}")
            return False
    
    def register_tool(self, platform: str, tool: CommunicationTool) -> None:
        """
        Register a new communication tool for a specific platform.
        
        Args:
            platform: The platform identifier (e.g., "telegram", "slack")
            tool: The communication tool instance
        """
        self._tools[platform.lower()] = tool
        logger.info(f"Registered tool for platform: {platform}")
    
    async def process_message(self, platform: str, user_id: str, message: str) -> Optional[str]:
        """
        Process a message using AI and return a response.
        
        Args:
            platform: The platform the message was received from
            user_id: Unique identifier for the user
            message: The message content
            
        Returns:
            Optional[str]: AI-generated response if successful, None otherwise
        """
        if not self.ai_model:
            logger.error("AI model not initialized")
            return None
            
        conversation_key = f"{platform}:{user_id}"
        
        # Initialize conversation history if needed
        if conversation_key not in self.conversation_history:
            self.conversation_history[conversation_key] = [
                Message(
                    role=MessageRole.SYSTEM,
                    content="You are a helpful AI assistant. Respond naturally and concisely."
                )
            ]
            
        # Add user message to history
        self.conversation_history[conversation_key].append(
            Message(role=MessageRole.USER, content=message)
        )
        
        try:
            # Get AI response
            response = await self.ai_model.chat(
                messages=self.conversation_history[conversation_key],
                temperature=0.7
            )
            
            # Add AI response to history
            self.conversation_history[conversation_key].append(
                Message(role=MessageRole.ASSISTANT, content=response.content)
            )
            
            return response.content
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None
    
    async def send_message(self, platform: str, recipient: str, message: str) -> bool:
        """
        Send a message using the specified platform.
        
        Args:
            platform: The platform to use for sending the message
            recipient: The recipient identifier
            message: The message content
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        platform = platform.lower()
        if platform not in self._tools:
            logger.error(f"No tool registered for platform: {platform}")
            return False
            
        return self._tools[platform].send_message(recipient, message)
    
    async def handle_incoming_message(self, platform: str, context: Dict[str, Any]) -> bool:
        """
        Handle an incoming message, process it with AI, and send a response.
        
        Args:
            platform: The platform the message was received from
            context: The message context/data
            
        Returns:
            bool: True if message was handled successfully, False otherwise
        """
        platform = platform.lower()
        if platform not in self._tools:
            logger.error(f"No tool registered for platform: {platform}")
            return False
            
        # Process the incoming message
        message_data = self._tools[platform].receive_message(context)
        if not message_data:
            return False
            
        # Extract user ID and message content (platform-specific)
        user_id = message_data.get("user_id")
        message = message_data.get("message")
        
        if not user_id or not message:
            logger.error("Missing user_id or message in message_data")
            return False
            
        # Get AI response
        response = await self.process_message(platform, user_id, message)
        if not response:
            return False
            
        # Send response back
        return await self.send_message(platform, user_id, response)
    
    def setup_channel(self, platform: str, params: Dict[str, Any]) -> bool:
        """
        Set up a communication channel for a specific platform.
        
        Args:
            platform: The platform to set up
            params: Platform-specific setup parameters
            
        Returns:
            bool: True if setup was successful, False otherwise
        """
        platform = platform.lower()
        if platform not in self._tools:
            logger.error(f"No tool registered for platform: {platform}")
            return False
            
        return self._tools[platform].setup_channel(params)
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        if self.ai_model:
            await self.ai_model.cleanup()
            self.ai_model = None

# Example usage
if __name__ == "__main__":
    # Create an instance of the Communications Agent
    agent = CommunicationsAgent()
    
    # Initialize the agent
    agent.initialize()
    
    # Example: Send a message via Telegram
    success = agent.send_message(
        platform="telegram",
        recipient="chat_id_here",
        message="Hello from Communications Agent!"
    )
    
    # Example: Set up Telegram webhook
    webhook_setup = agent.setup_channel(
        platform="telegram",
        params={"webhook_url": "https://your-domain.com/webhook"}
    )
