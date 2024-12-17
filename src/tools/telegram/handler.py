from typing import Dict, Any
from .base import TelegramBaseTool
from ..ollama.chat import OllamaChatTool
from src.tools.templates.tool_template import ToolResponse
import json
import logging

logger = logging.getLogger(__name__)

class TelegramHandler(TelegramBaseTool):
    """
    Tool for handling Telegram messages with AI integration.
    Passes messages directly between Telegram and Ollama.
    """
    
    def __init__(self):
        super().__init__()
        self.ollama = OllamaChatTool()
        
    def get_schema(self) -> Dict[str, Any]:
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
        """Execute the Telegram handler with AI integration"""
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
        """Handle a Telegram update"""
        update = params["update"]
        if not update.get("message") or not update["message"].get("text"):
            return ToolResponse(success=False, error="No message text found")
            
        # Extract message details
        message = update["message"]
        chat_id = str(message["chat"]["id"])
        user_message = message["text"]
        logger.info(f"Processing message '{user_message}' from chat {chat_id}")
        
        # Get AI response
        logger.info("Sending to Ollama...")
        ai_response = await self.ollama.execute({
            "model": "llama3.2",
            "messages": [
                {
                    "role": "system",
                    "content": "You are Farda's AI assistant. Always respond respectfully and end your messages with 'sir'. Keep responses helpful but concise."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        })
        logger.info(f"Ollama response: {json.dumps(ai_response.__dict__, indent=2)}")
        
        if not ai_response.success:
            error_msg = f"Failed to get AI response: {ai_response.error}"
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg
            )
        
        # Extract AI message
        ai_message = ai_response.data["message"]["content"]
        logger.info(f"Sending message back to Telegram: {ai_message}")
        
        # Send response back to user
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=ai_message
            )
            logger.info("Message sent successfully")
            
            return ToolResponse(success=True, data={
                "sent_message": ai_message
            })
        except Exception as e:
            error_msg = f"Failed to send message: {str(e)}"
            logger.error(error_msg)
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
    
    async def process_update(self, params: Dict[str, Any]) -> ToolResponse:
        """Process a webhook update from Telegram"""
        try:
            await self.ensure_initialized(params["token"])
            update = params["update"]
            
            if not update.get("message") or not update["message"].get("text"):
                logger.error("No message text found in update")
                return ToolResponse(success=False, error="No message text found")
            
            # Extract message details
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message["text"]
            
            logger.info(f"Processing message '{text}' from chat {chat_id}")
            
            # Get AI response from Ollama
            logger.info("Sending to Ollama...")
            ollama_response = await self.ollama.execute({
                "messages": [{"role": "user", "content": text}]
            })
            
            if not ollama_response.success:
                error_msg = f"Ollama error: {ollama_response.error}"
                logger.error(error_msg)
                return ToolResponse(success=False, error=error_msg)
            
            # Extract AI response
            ai_message = ollama_response.data["message"]["content"]
            logger.info(f"Got response from Ollama: {ai_message}")
            
            # Send response back to Telegram
            logger.info("Sending response to Telegram...")
            await self.bot.send_message(chat_id=chat_id, text=ai_message)
            logger.info("Response sent successfully")
            
            return ToolResponse(success=True, data={
                "chat_id": chat_id,
                "response": ai_message
            })
            
        except Exception as e:
            error_msg = f"Error processing update: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg)
