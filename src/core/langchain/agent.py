"""
LangChain Agent Integration

This module provides the core LangChain agent implementation for GodFarda.
"""

from typing import Any, Dict, List, Optional
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, LLMResult
from .llm import OllamaLLM
from .memory import GodFardaMemory
from .tools import register_langchain_tools
import logging

logger = logging.getLogger(__name__)

class GodFardaCallback(BaseCallbackHandler):
    """Callback handler for GodFarda agent execution."""
    
    def on_llm_start(self, *args, **kwargs) -> None:
        """Handle LLM start event."""
        logger.debug("LLM started processing")
    
    def on_llm_end(self, response: LLMResult, *args, **kwargs) -> None:
        """Handle LLM end event."""
        logger.debug("LLM finished processing")
    
    def on_tool_start(self, action: AgentAction, *args, **kwargs) -> None:
        """Handle tool start event."""
        logger.info(f"Starting tool execution: {action.tool}")
    
    def on_tool_end(self, *args, **kwargs) -> None:
        """Handle tool end event."""
        logger.info("Tool execution completed")
    
    def on_agent_action(self, action: AgentAction, *args, **kwargs) -> Any:
        """Handle agent action event."""
        logger.info(f"Agent executing action: {action.tool}")

class LangChainAgent:
    """LangChain-based agent implementation."""
    
    def __init__(self, model_name: str = "llama2", **kwargs):
        """Initialize the LangChain agent.
        
        Args:
            model_name: Name of the Ollama model to use
            **kwargs: Additional arguments for agent configuration
        """
        self.llm = OllamaLLM(model=model_name)
        self.memory = GodFardaMemory()
        self.tools = register_langchain_tools()
        self.callback = GodFardaCallback()
        
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            callbacks=[self.callback],
            **kwargs
        )
    
    async def process_message(self, message: str, user_info: Optional[Dict[str, Any]] = None) -> str:
        """Process a message using the LangChain agent.
        
        Args:
            message: The input message to process
            user_info: Optional user information to store in memory
            
        Returns:
            The agent's response
        """
        try:
            # Add user info to memory if provided
            inputs = {"input": message}
            if user_info:
                inputs["user_info"] = user_info
            
            response = await self.agent.arun(**inputs)
            return response
        
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"I encountered an error while processing your message: {str(e)}"
    
    def clear_memory(self) -> None:
        """Clear the agent's memory."""
        self.memory.clear()
