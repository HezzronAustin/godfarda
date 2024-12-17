from typing import Dict, Any
from telegram.error import TelegramError
from .base import TelegramBaseTool
from src.tools.templates.tool_template import ToolResponse

class TelegramMessageTool(TelegramBaseTool):
    """
    Tool for handling Telegram message operations.
    Provides functionality to send messages and receive updates through a Telegram bot.
    """
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Define the parameter schema for the Telegram message tool
        
        Returns:
            Dict containing the parameter schema with supported actions and required fields
        """
        return {
            "action": {
                "type": "string",
                "enum": ["send_message", "get_updates"],
                "description": "Action to perform (send_message or get_updates)"
            },
            "chat_id": {
                "type": "string",
                "description": "Telegram chat ID to send message to"
            },
            "message": {
                "type": "string",
                "description": "Message text to send (required for send_message action)"
            },
            "token": {
                "type": "string",
                "description": "Telegram Bot API token"
            }
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        """
        Execute the requested Telegram message action
        
        Args:
            params: Dictionary containing action and required parameters
            
        Returns:
            ToolResponse with success status and relevant data or error message
        """
        try:
            await self.ensure_initialized(params["token"])
                
            if params["action"] == "send_message":
                return await self._send_message(params)
            elif params["action"] == "get_updates":
                return await self._get_updates()
                
            return ToolResponse(success=False, error="Invalid action specified")
            
        except Exception as e:
            return ToolResponse(success=False, error=self.format_error(e))
            
    async def _send_message(self, params: Dict[str, Any]) -> ToolResponse:
        """Handle send_message action"""
        if not params.get("message"):
            return ToolResponse(success=False, error="Message parameter is required for send_message action")
            
        result = await self.bot.send_message(
            chat_id=params["chat_id"],
            text=params["message"]
        )
        
        return ToolResponse(success=True, data={
            "message_id": result.message_id,
            "chat_id": result.chat.id,
            "date": result.date.isoformat()
        })
        
    async def _get_updates(self) -> ToolResponse:
        """Handle get_updates action"""
        updates = await self.bot.get_updates()
        formatted_updates = []
        
        for update in updates:
            update_data = {
                "update_id": update.update_id,
                "message": None
            }
            
            if update.message:
                update_data["message"] = {
                    "message_id": update.message.message_id,
                    "chat": {
                        "id": update.message.chat.id,
                        "type": update.message.chat.type,
                        "username": update.message.chat.username
                    },
                    "text": update.message.text,
                    "date": update.message.date.isoformat()
                }
            
            formatted_updates.append(update_data)
        
        return ToolResponse(success=True, data={"updates": formatted_updates})
