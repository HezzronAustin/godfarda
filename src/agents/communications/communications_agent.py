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
from src.agents.base import BaseAgent, AgentConfig
from .memory.memory_store import CommunicationsMemory

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
        """Set up the communication channel."""
        pass

class TelegramToolAdapter(CommunicationTool):
    """Adapter for the existing TelegramHandler to match CommunicationTool interface."""
    
    def __init__(self):
        self.handler = TelegramHandler()
    
    def send_message(self, recipient: str, message: str) -> bool:
        try:
            self.handler.send_message(recipient, message)
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def receive_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.handler.handle_message(context)
    
    def setup_channel(self, params: Dict[str, Any]) -> bool:
        try:
            self.handler.initialize()
            return True
        except Exception as e:
            logger.error(f"Error setting up Telegram channel: {e}")
            return False

class CommunicationsAgent(BaseAgent):
    """Main Communications Agent class that orchestrates messaging across different platforms."""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._tools: Dict[str, CommunicationTool] = {}
        self.memory = CommunicationsMemory()
        
        # Register the Telegram tool by default
        self.register_tool("telegram", TelegramToolAdapter())
        
        # Initialize AI model
        self.ai_model: Optional[AIModel] = None
        self.ai_model_name = config.get("ai_model_name", "ollama")
        self.ai_model_params = config.get("ai_model_params", {})
        
        # Conversation history for AI context
        self.conversation_history: Dict[str, List[Message]] = {}
    
    def initialize(self):
        """Initialize the agent and its AI model."""
        try:
            self.ai_model = AIModelFactory.create_model(self.ai_model_name, **self.ai_model_params)
            logger.info(f"Initialized AI model: {self.ai_model_name}")
            return True
        except Exception as e:
            logger.error(f"Error initializing AI model: {e}")
            return False
    
    def register_tool(self, platform: str, tool: CommunicationTool):
        """
        Register a new communication tool for a specific platform.
        
        Args:
            platform: The platform identifier (e.g., "telegram", "slack")
            tool: The communication tool instance
        """
        self._tools[platform] = tool
        logger.info(f"Registered communication tool for platform: {platform}")
    
    def process_message(self, platform: str, user_id: str, message: str) -> Optional[str]:
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
        
        try:
            # Get conversation history
            history = self.conversation_history.get(user_id, [])
            
            # Add user message to history
            history.append(Message(role=MessageRole.USER, content=message))
            
            # Get AI response
            response: ModelResponse = self.ai_model.chat(history)
            if response and response.message:
                # Add AI response to history
                history.append(response.message)
                
                # Update conversation history
                self.conversation_history[user_id] = history
                
                # Store the interaction in memory
                self.memory.store_conversation(platform, user_id, message, response.message.content)
                
                return response.message.content
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
        
        return None
    
    def send_message(self, platform: str, recipient: str, message: str) -> bool:
        """
        Send a message using the specified platform.
        
        Args:
            platform: The platform to use for sending the message
            recipient: The recipient identifier
            message: The message content
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if platform not in self._tools:
            logger.error(f"No tool registered for platform: {platform}")
            return False
        
        return self._tools[platform].send_message(recipient, message)
    
    def handle_incoming_message(self, platform: str, context: Dict[str, Any]) -> bool:
        """
        Handle an incoming message, process it with AI, and send a response.
        
        Args:
            platform: The platform the message was received from
            context: The message context/data
            
        Returns:
            bool: True if message was handled successfully, False otherwise
        """
        if platform not in self._tools:
            logger.error(f"No tool registered for platform: {platform}")
            return False
        
        try:
            # Process the incoming message
            message_data = self._tools[platform].receive_message(context)
            if not message_data:
                return False
            
            user_id = message_data.get("user_id")
            message = message_data.get("message")
            
            if not user_id or not message:
                logger.error("Missing user_id or message in processed data")
                return False
            
            # Get AI response
            response = self.process_message(platform, user_id, message)
            if response:
                # Send the response back
                return self.send_message(platform, user_id, response)
            
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")
        
        return False
    
    def setup_channel(self, platform: str, params: Dict[str, Any]) -> bool:
        """
        Set up a communication channel for a specific platform.
        
        Args:
            platform: The platform to set up
            params: Platform-specific setup parameters
            
        Returns:
            bool: True if setup was successful, False otherwise
        """
        if platform not in self._tools:
            logger.error(f"No tool registered for platform: {platform}")
            return False
        
        return self._tools[platform].setup_channel(params)
    
    def cleanup(self):
        """Clean up resources used by the agent."""
        # Clean up AI model if needed
        if self.ai_model and hasattr(self.ai_model, 'cleanup'):
            self.ai_model.cleanup()
        
        # Clear conversation history
        self.conversation_history.clear()
