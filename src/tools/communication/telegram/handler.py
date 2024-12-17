from typing import Dict, Any, Optional
from .base import TelegramBaseTool
from src.tools.ai.ollama.chat import OllamaChatTool
from src.tools.templates.tool_template import ToolResponse
from src.core.trigger_monitor.trigger_monitor import get_trigger_monitor
from src.core.events import EventManager, EventType, EventPlatform, EventCategory
from .trigger import TelegramTrigger
from .process_manager import ensure_single_instance
import json
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

class TelegramHandler(TelegramBaseTool):
    """Handler for Telegram messages with Godfarda integration"""
    
    def __init__(self):
        super().__init__()
        # Import GodFarda here to avoid circular import
        from src.agents.godfarda.godfarda_agent import GodFarda, AgentConfig
        # Initialize Godfarda agent
        self.godfarda = GodFarda(AgentConfig(
            name="godfarda",
            allowed_tools=["OllamaChatTool", "codebase_search", "edit_file", "view_file"],
            parameters={"model": "llama3.2:latest"}
        ))
        # Keep Ollama for error handling and fallback
        self.ollama = OllamaChatTool()
        # Initialize trigger monitoring
        self.trigger_monitor = get_trigger_monitor()
        self.telegram_trigger = TelegramTrigger()
        self.trigger_monitor.register_trigger(self.telegram_trigger)
        # Initialize event manager
        self.event_manager = EventManager()
        
    async def initialize(self, token: str):
        """Initialize the handler and Godfarda agent"""
        try:
            # Ensure no other bot instances are running
            ensure_single_instance()
            
            await super().initialize(token)
            # Initialize Godfarda
            if not await self.godfarda.initialize():
                error_msg = "Failed to initialize Godfarda agent"
                logger.error(error_msg)
                # Try to send error message to admin chat if configured
                try:
                    admin_chat = os.getenv('TELEGRAM_ADMIN_CHAT')
                    if admin_chat and self.bot:
                        await self.bot.send_message(
                            chat_id=admin_chat,
                            text=f"🚨 Bot Error: {error_msg}"
                        )
                except Exception as e:
                    logger.error(f"Failed to send admin notification: {e}")
                raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Failed to initialize Telegram handler: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)
            
    async def get_schema(self) -> Dict[str, Any]:
        """Define the parameter schema for the Telegram handler"""
        return {
            "action": {
                "type": "string",
                "enum": ["handle_update", "setup_webhook", "process_update"],
                "description": "Action to perform"
            },
            "token": {
                "type": "string",
                "description": "Telegram Bot API token"
            },
            "update": {
                "type": "object",
                "description": "Telegram update object"
            },
            "webhook_url": {
                "type": "string",
                "description": "Webhook URL for receiving Telegram updates"
            }
        }
        
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        """Execute the Telegram handler with Godfarda integration"""
        try:
            await self.ensure_initialized(params["token"])
            
            if params["action"] == "handle_update":
                return await self.handle_update(params)
            elif params["action"] == "setup_webhook":
                return await self.setup_webhook(params)
            elif params["action"] == "process_update":
                return await self.process_update(params)
            else:
                return ToolResponse(success=False, error="Invalid action")
                
        except Exception as e:
            error_msg = f"Handler error: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg)
            
    async def handle_update(self, params: Dict[str, Any]) -> ToolResponse:
        """Handle a Telegram update by forwarding to Godfarda"""
        try:
            update = params["update"]
            if not update.get("message") or not update["message"].get("text"):
                return ToolResponse(success=False, error="No message text found")
                
            # Extract message details
            message = update["message"]
            chat_id = str(message["chat"]["id"])
            user_message = message["text"]
            user_info = {
                "username": message["from"].get("username", "unknown"),
                "first_name": message["from"].get("first_name", ""),
                "last_name": message["from"].get("last_name", ""),
                "chat_id": chat_id,
                "message_id": message["message_id"]
            }
            
            logger.info(f"Forwarding message to Godfarda from {user_info['username']}: {user_message}")
            
            try:
                # Process message through Godfarda
                response = await self.godfarda.process({
                    "message": user_message,
                    "user_info": user_info,
                    "platform": "telegram"
                })
                
                if "error" in response:
                    return await self.handle_error(chat_id, response["error"])
                    
                # Show typing animation and send response
                await self.send_typing_action(int(chat_id))
                await asyncio.sleep(1.5)  # Shorter typing delay
                
                sent_message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=response["response"],
                    reply_to_message_id=message["message_id"]
                )
                
                return ToolResponse(success=True, data={
                    "agent": response.get("agent", "godfarda"),
                    "response": response["response"],
                    "user": user_info,
                    "message_id": sent_message.message_id
                })
                
            except Exception as e:
                return await self.handle_error(chat_id, str(e))
                
        except Exception as e:
            error_msg = f"Failed to process message: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg)
            
    async def handle_message(self, message: Dict[str, Any]) -> ToolResponse:
        """Handle an incoming Telegram message"""
        try:
            chat_id = str(message["chat"]["id"])
            user_info = {
                "id": str(message.get("from", {}).get("id", "unknown")),
                "username": message.get("from", {}).get("username", "unknown"),
                "first_name": message.get("from", {}).get("first_name", ""),
                "last_name": message.get("from", {}).get("last_name", "")
            }
            user_message = message.get("text", "")
            
            logger.info(f"Received message from {user_info['username']} (ID: {user_info['id']}): {user_message}")
            
            if not user_message:
                error_msg = "Empty message received"
                logger.warning(error_msg)
                return ToolResponse(success=False, error=error_msg)
            
            context = {
                "chat_id": chat_id,
                "user": user_info,
                "message_id": message["message_id"]
            }
            
            logger.info(f"Processing message with context: {json.dumps(context, indent=2)}")
            
            try:
                # Process message through Godfarda
                logger.debug("Sending message to Godfarda for processing...")
                response = await self.godfarda.process({
                    "message": user_message,
                    "user_info": user_info,
                    "platform": "telegram"
                })
                
                if "error" in response:
                    error_msg = f"Godfarda processing error: {response['error']}"
                    logger.error(error_msg)
                    return await self.handle_error(chat_id, error_msg)
                
                logger.info(f"Godfarda processed message successfully: {json.dumps(response, indent=2)}")
                
                # Show typing animation and send response
                await self.send_typing_action(int(chat_id))
                await asyncio.sleep(1.5)  # Shorter typing delay
                
                sent_message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=response["response"],
                    reply_to_message_id=message["message_id"]
                )
                
                logger.info(f"Sent response to user {user_info['username']}: {response['response'][:100]}...")
                
                return ToolResponse(success=True, data={
                    "agent": response.get("agent", "godfarda"),
                    "response": response["response"],
                    "user": user_info,
                    "message_id": sent_message.message_id
                })
                
            except Exception as e:
                error_msg = f"Error processing message through Godfarda: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return await self.handle_error(chat_id, error_msg)
                
        except Exception as e:
            error_msg = f"Failed to process message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Try to send error message to user
            try:
                if chat_id:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=f"🚨 Error: Something went wrong while processing your message. Please try again later."
                    )
            except Exception as send_error:
                logger.error(f"Failed to send error message to user: {send_error}")
            return ToolResponse(success=False, error=error_msg)
            
    async def handle_error(self, chat_id: str, error: str) -> ToolResponse:
        """Handle errors with a friendly AI response"""
        try:
            logger.error(f"Handling error: {error}")
            
            # Get AI response for error handling
            try:
                error_response = await self.ollama.execute({
                    "model": "llama3.2",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant. An error has occurred. Please provide a friendly and helpful response."
                        },
                        {
                            "role": "user",
                            "content": f"Error: {error}\n\nPlease provide a friendly response to the user explaining the error."
                        }
                    ]
                })
                
                friendly_message = error_response.get("response", 
                    "I apologize, but I encountered an error while processing your request. "
                    "The development team has been notified. Please try again later.")
                
            except Exception as e:
                logger.error(f"Failed to get AI error response: {e}", exc_info=True)
                friendly_message = ("I apologize, but I encountered an error while processing your request. "
                                 "The development team has been notified. Please try again later.")
            
            # Send error message to user
            await self.bot.send_message(
                chat_id=chat_id,
                text=f"🤖 {friendly_message}\n\n🔍 Technical details: {error}"
            )
            
            # Notify admin if configured
            try:
                admin_chat = os.getenv('TELEGRAM_ADMIN_CHAT')
                if admin_chat:
                    await self.bot.send_message(
                        chat_id=admin_chat,
                        text=f"🚨 Error Report\n\nChat: {chat_id}\nError: {error}"
                    )
            except Exception as e:
                logger.error(f"Failed to send admin notification: {e}")
            
            return ToolResponse(success=False, error=error)
            
        except Exception as e:
            logger.error(f"Error in handle_error: {e}", exc_info=True)
            return ToolResponse(success=False, error=f"Error handler failed: {str(e)}")
            
    async def process_update(self, update: Dict[str, Any]) -> ToolResponse:
        """Process a Telegram update"""
        try:
            # Log the update for debugging
            logger.debug(f"Processing update: {json.dumps(update, indent=2)}")
            
            # Trigger webhook received event
            self.event_manager.trigger_event(
                event_type=EventType.WEBHOOK_RECEIVED,
                platform=EventPlatform.TELEGRAM,
                category=EventCategory.WEBHOOK,
                body={
                    "update_id": update.get("update_id"),
                    "raw_update": update
                }
            )
            
            if "message" in update:
                message = update["message"]
                if "text" in message:
                    return await self.handle_update({
                        "update": update,
                        "token": self.token
                    })
                else:
                    logger.warning("Received message without text")
                    return ToolResponse(success=False, error="Message has no text content")
            elif "callback_query" in update:
                return await self.handle_callback_query(update["callback_query"])
            else:
                logger.warning(f"Unsupported update type: {update}")
                return ToolResponse(success=False, error="Unsupported update type")
                
        except Exception as e:
            error_msg = f"Error processing update: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ToolResponse(success=False, error=error_msg)
            
    async def setup_webhook(self, params: Dict[str, Any]) -> ToolResponse:
        """Set up webhook for receiving Telegram updates"""
        try:
            await self.ensure_initialized(params["token"])
            webhook_url = params["webhook_url"]
            
            # Remove any existing webhook
            await self.bot.delete_webhook()
            
            # Set the new webhook
            await self.bot.set_webhook(url=webhook_url)
            
            return ToolResponse(success=True, data={"message": f"Webhook set to {webhook_url}"})
            
        except Exception as e:
            return ToolResponse(success=False, error=self.format_error(e))
