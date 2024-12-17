"""
Ollama LLM Integration for LangChain

This module provides a custom LangChain LLM implementation for Ollama.
"""

from typing import Any, Dict, List, Optional, Iterator
import aiohttp
import json
import logging
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.schema.output import GenerationChunk

logger = logging.getLogger(__name__)

class OllamaLLM(LLM):
    """Custom LangChain LLM implementation for Ollama."""
    
    model_name: str = "llama2"
    base_url: str = "http://localhost:11434/api"
    temperature: float = 0.7
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "ollama"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the LLM call."""
        try:
            # Create async event loop for sync call
            import asyncio
            return asyncio.run(self._acall(prompt, stop, run_manager, **kwargs))
        except Exception as e:
            logger.error(f"Error in Ollama LLM call: {e}")
            raise

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Execute the async LLM call."""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    **kwargs
                }
                
                if stop:
                    data["stop"] = stop

                async with session.post(
                    f"{self.base_url}/generate",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error (Status {response.status}): {error_text}")
                    
                    result = await response.json()
                    return result.get("response", "")
                    
        except Exception as e:
            logger.error(f"Error in async Ollama LLM call: {e}")
            raise

    async def _astream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        """Stream the LLM response."""
        try:
            async with aiohttp.ClientSession() as session:
                data = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "temperature": self.temperature,
                    "stream": True,
                    **kwargs
                }
                
                if stop:
                    data["stop"] = stop

                async with session.post(
                    f"{self.base_url}/generate",
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error (Status {response.status}): {error_text}")
                    
                    async for line in response.content:
                        if line:
                            try:
                                result = json.loads(line)
                                if "response" in result:
                                    yield GenerationChunk(text=result["response"])
                            except json.JSONDecodeError:
                                continue
                    
        except Exception as e:
            logger.error(f"Error in Ollama stream: {e}")
            raise
