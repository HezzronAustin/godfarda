"""
Ollama Model Implementation

This module implements the AIModel interface for Ollama models.
"""

import aiohttp
from typing import Dict, Any, List, Optional
import logging
from ..base import AIModel, Message, ModelResponse, MessageRole, AIModelFactory

logger = logging.getLogger(__name__)

class OllamaModel(AIModel):
    """Ollama implementation of the AIModel interface"""
    
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434/api"):
        self.model_name = model_name
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self) -> bool:
        """Initialize aiohttp session and verify Ollama connection"""
        try:
            self.session = aiohttp.ClientSession()
            # Test connection
            async with self.session.get(f"{self.base_url}/tags") as response:
                if response.status != 200:
                    logger.error(f"Failed to connect to Ollama API: {response.status}")
                    return False
                return True
        except Exception as e:
            logger.error(f"Error initializing Ollama model: {e}")
            return False
    
    async def chat(self,
                  messages: List[Message],
                  temperature: float = 0.7,
                  max_tokens: Optional[int] = None,
                  **kwargs) -> ModelResponse:
        """Send chat request to Ollama"""
        if not self.session:
            raise RuntimeError("Model not initialized. Call initialize() first.")
            
        # Convert messages to Ollama format
        ollama_messages = [
            {
                "role": msg.role.value,
                "content": msg.content,
                **({"name": msg.name} if msg.name else {})
            }
            for msg in messages
        ]
        
        data = {
            "model": self.model_name,
            "messages": ollama_messages,
            "temperature": temperature,
            **({"max_tokens": max_tokens} if max_tokens else {}),
            **kwargs
        }
        
        try:
            async with self.session.post(f"{self.base_url}/chat", json=data) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                    
                result = await response.json()
                
                return ModelResponse(
                    content=result["message"]["content"],
                    model=self.model_name,
                    usage={
                        "prompt_tokens": result.get("prompt_eval_count", 0),
                        "completion_tokens": result.get("eval_count", 0),
                        "total_tokens": result.get("total_eval_count", 0)
                    },
                    raw_response=result
                )
                
        except Exception as e:
            logger.error(f"Error in Ollama chat: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

# Register Ollama model with the factory
AIModelFactory.register("ollama", OllamaModel)
