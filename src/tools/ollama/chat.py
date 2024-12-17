from typing import Dict, Any, List
import aiohttp
import json
import logging
from src.tools.templates.tool_template import BaseTool, ToolResponse

logger = logging.getLogger(__name__)

class OllamaChatTool(BaseTool):
    """Tool for interacting with Ollama's chat functionality"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "http://localhost:11434/api"
        
    def get_schema(self) -> Dict[str, Any]:
        """Define the parameter schema for the Ollama chat tool"""
        return {
            "model": {
                "type": "string",
                "description": "Name of the Ollama model to use",
                "default": "llama3.2"
            },
            "messages": {
                "type": "array",
                "description": "List of message objects with 'role' and 'content'",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["system", "user", "assistant"]
                        },
                        "content": {
                            "type": "string"
                        }
                    }
                }
            },
            "stream": {
                "type": "boolean",
                "description": "Whether to stream the response",
                "default": False
            }
        }
        
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        """
        Execute a chat request to Ollama
        
        Args:
            params: Dictionary containing model, messages, and stream parameters
            
        Returns:
            ToolResponse with the chat response
        """
        try:
            model = params.get("model", "llama3.2")
            messages = params.get("messages", [])
            stream = params.get("stream", False)
            
            if not messages:
                return ToolResponse(success=False, error="No messages provided")
            
            # Convert messages to Ollama format
            formatted_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    # Prepend system message to first user message
                    continue
                formatted_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Add system message as a prefix to the first user message if it exists
            system_message = next((msg["content"] for msg in messages if msg["role"] == "system"), None)
            if system_message and formatted_messages:
                for msg in formatted_messages:
                    if msg["role"] == "user":
                        msg["content"] = f"{system_message}\n\nUser: {msg['content']}"
                        break
            
            logger.info(f"Sending request to Ollama - Model: {model}, Messages: {json.dumps(formatted_messages, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat",
                    json={
                        "model": model,
                        "messages": formatted_messages,
                        "stream": stream
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        error_msg = f"Ollama API error: {error_text}"
                        logger.error(error_msg)
                        return ToolResponse(success=False, error=error_msg)
                    
                    result = await response.json()
                    logger.info(f"Received response from Ollama: {json.dumps(result, indent=2)}")
                    
                    return ToolResponse(
                        success=True,
                        data={
                            "message": result.get("message", {}),
                            "model": result.get("model", model)
                        }
                    )
                    
        except Exception as e:
            error_msg = f"Failed to execute Ollama chat: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg)
