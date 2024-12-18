from typing import Dict, Set, Any, Callable, Awaitable, Optional
from pydantic import BaseModel
from ..models.base import ToolPermission
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Tool(BaseModel):
    name: str
    description: str
    permission: ToolPermission
    func: Callable[..., Awaitable[Any]]
    is_async: bool = True
    resource_cost: float = 0.0
    
    class Config:
        arbitrary_types_allowed = True

class ToolManager:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.running_tools: Dict[str, asyncio.Task] = {}
        
    def register_tool(self, tool: Tool):
        if tool.name in self.tools:
            raise ValueError(f"Tool {tool.name} already registered")
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        
    async def execute_tool(
        self,
        tool_name: str,
        permissions: Set[str],
        **kwargs
    ) -> Any:
        tool = self.tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool {tool_name} not found")
            
        if tool.permission.name not in permissions:
            raise PermissionError(
                f"Missing permission {tool.permission.name} for tool {tool_name}"
            )
            
        try:
            if tool.is_async:
                result = await tool.func(**kwargs)
            else:
                result = await asyncio.to_thread(tool.func, **kwargs)
                
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            raise
            
    def get_available_tools(self, permissions: Set[str]) -> Dict[str, Tool]:
        return {
            name: tool
            for name, tool in self.tools.items()
            if tool.permission.name in permissions
        }
        
    async def monitor_resources(self):
        while True:
            current_cost = sum(
                tool.resource_cost
                for task in self.running_tools.values()
                if not task.done()
            )
            logger.info(f"Current resource usage: {current_cost}")
            await asyncio.sleep(60)  # Monitor every minute
