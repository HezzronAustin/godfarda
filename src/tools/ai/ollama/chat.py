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
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the Ollama chat tool by checking if the service is available"""
        try:
            logger.info("Initializing Ollama chat tool...")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/tags") as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Failed to initialize Ollama: {error_text}")
                        return False
                    
                    # Check if our model is available
                    tags = await response.json()
                    models = [model['name'] for model in tags.get('models', [])]
                    logger.info(f"Available Ollama models: {models}")
                    
                    if not any(model.startswith("llama") for model in models):
                        logger.error("No Llama model found in Ollama")
                        return False
                    
                    self._initialized = True
                    logger.info("Ollama chat tool initialized successfully")
                    return True
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to connect to Ollama service: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error initializing Ollama: {e}", exc_info=True)
            return False
        
    def get_schema(self) -> Dict[str, Any]:
        """Define the parameter schema for the Ollama chat tool"""
        return {
            "model": {
                "type": "string",
                "description": "Name of the Ollama model to use",
                "default": "llama3.2:latest"
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
        if not self._initialized:
            try:
                if not await self.initialize():
                    return ToolResponse(
                        success=False,
                        error="Ollama service is not available. Please ensure Ollama is running and try again."
                    )
            except Exception as e:
                error_msg = f"Failed to initialize Ollama: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return ToolResponse(success=False, error=error_msg)
        
        try:
            model = params.get("model", "llama3.2:latest")
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
            
            logger.debug(f"Sending request to Ollama - Model: {model}, Messages: {json.dumps(formatted_messages)}")
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        f"{self.base_url}/chat",
                        json={
                            "model": model,
                            "messages": formatted_messages,
                            "stream": stream
                        },
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            error_msg = f"Ollama API error (Status {response.status}): {error_text}"
                            logger.error(error_msg)
                            return ToolResponse(success=False, error=error_msg)
                        
                        result = await response.json()
                        logger.debug(f"Received response from Ollama: {json.dumps(result)}")
                        
                        return ToolResponse(success=True, data={
                            "response": result.get("message", {}).get("content", ""),
                            "model": model
                        })
                except aiohttp.ClientError as e:
                    error_msg = f"Failed to communicate with Ollama service: {str(e)}"
                    logger.error(error_msg)
                    return ToolResponse(success=False, error=error_msg)
                
        except Exception as e:
            error_msg = f"Unexpected error in Ollama chat: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ToolResponse(success=False, error=error_msg)
