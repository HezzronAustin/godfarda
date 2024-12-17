from typing import Dict, Any
from .base import TelegramBaseTool
from src.tools.ai.ollama.chat import OllamaChatTool
from src.tools.templates.tool_template import ToolResponse
from src.agents.godfarda.godfarda_agent import GodFarda, AgentConfig
from src.core.trigger_monitor.trigger_monitor import get_trigger_monitor
from src.core.events import EventManager, EventType, EventPlatform, EventCategory
from .trigger import TelegramTrigger
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class TelegramHandler(TelegramBaseTool):
    """Handler for Telegram messages with Godfarda integration"""
    
    def __init__(self):
        super().__init__()
        # Initialize Godfarda agent
        self.godfarda = GodFarda(AgentConfig(
            name="godfarda",
            allowed_tools=["ollama_chat", "codebase_search", "edit_file", "view_file"],
            parameters={"model": "llama3.2"}
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
        await super().initialize(token)
        # Initialize Godfarda
        if not await self.godfarda.initialize():
            logger.error("Failed to initialize Godfarda agent")
            raise RuntimeError("Godfarda initialization failed")
            
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
            
    async def handle_error(self, chat_id: str, error: str) -> ToolResponse:
        """Handle errors with a friendly AI response"""
        try:
            logger.error(f"Error occurred: {error}")
            
            # Get AI response for error handling
            error_response = await self.ollama.execute({
                "model": "llama3.2",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant handling an error. Respond in a friendly and helpful way, explaining the issue and suggesting next steps."
                    },
                    {
                        "role": "user",
                        "content": f"An error occurred: {error}. Please provide a user-friendly response."
                    }
                ]
            })
            
            if error_response.success:
                error_message = error_response.data["message"]["content"]
            else:
                error_message = f"I encountered an error: {error}. Please try again later."
            
            await self.send_typing_action(int(chat_id))
            await asyncio.sleep(1)
            await self.bot.send_message(chat_id=chat_id, text=error_message)
            
            return ToolResponse(success=False, error=error, data={
                "friendly_message": error_message
            })
            
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}")
            return ToolResponse(success=False, error=str(e))
            
    async def handle_message(self, message: Dict[str, Any]) -> ToolResponse:
        """Handle an incoming Telegram message"""
        try:
            # Trigger message received event
            self.event_manager.trigger_event(
                event_type=EventType.MESSAGE_RECEIVED,
                platform=EventPlatform.TELEGRAM,
                category=EventCategory.COMMUNICATION,
                body={
                    "chat_id": message.get("chat", {}).get("id"),
                    "user_id": message.get("from", {}).get("id"),
                    "text": message.get("text", ""),
                    "message_id": message.get("message_id"),
                    "raw_message": message
                }
            )
            
            # Process message with Godfarda
            response = await self.godfarda.process(message)
            
            # Trigger AI response event
            self.event_manager.trigger_event(
                event_type=EventType.AI_RESPONDED,
                platform=EventPlatform.TELEGRAM,
                category=EventCategory.AI_INTERACTION,
                body={
                    "chat_id": message.get("chat", {}).get("id"),
                    "user_id": message.get("from", {}).get("id"),
                    "response": response,
                    "original_message": message
                }
            )
            
            return ToolResponse(success=True, data=response)
            
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            # Trigger error event
            self.event_manager.trigger_event(
                event_type=EventType.MESSAGE_RECEIVED,
                platform=EventPlatform.TELEGRAM,
                category=EventCategory.SYSTEM,
                body={
                    "error": str(e),
                    "chat_id": message.get("chat", {}).get("id"),
                    "message_id": message.get("message_id")
                }
            )
            return ToolResponse(success=False, error=str(e))

    async def process_update(self, update: Dict[str, Any]) -> ToolResponse:
        """Process a Telegram update"""
        try:
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
                return await self.handle_message(update["message"])
            elif "callback_query" in update:
                return await self.handle_callback_query(update["callback_query"])
            else:
                logger.warning(f"Unsupported update type: {update}")
                return ToolResponse(success=False, error="Unsupported update type")
                
        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            return ToolResponse(success=False, error=str(e))
            
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
