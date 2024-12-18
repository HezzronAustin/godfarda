from typing import Dict, Any, Optional, List
from uuid import UUID
import asyncio
from pydantic import BaseModel
from ..models.base import ChainableMinion, AgentState
from ..tools.manager import ToolManager
import logging

logger = logging.getLogger(__name__)

class Task(BaseModel):
    id: UUID
    query: str
    context: Dict[str, Any]
    requires_capabilities: set[str]
    parent_task_id: Optional[UUID] = None

class MinionAgent:
    def __init__(
        self,
        minion: ChainableMinion,
        tool_manager: ToolManager
    ):
        self.minion = minion
        self.tool_manager = tool_manager
        self.tasks: Dict[UUID, Task] = {}
        
    async def can_handle_task(self, task: Task) -> bool:
        return all(
            cap in self.minion.capabilities
            for cap in task.requires_capabilities
        )
        
    async def delegate_task(self, task: Task) -> Optional[ChainableMinion]:
        for child in self.minion.children.values():
            child_agent = MinionAgent(child, self.tool_manager)
            if await child_agent.can_handle_task(task):
                return child
        return None
        
    async def process_task(self, task: Task) -> Dict[str, Any]:
        self.tasks[task.id] = task
        
        # Check if we can handle it
        if not await self.can_handle_task(task):
            # Try to delegate
            child = await self.delegate_task(task)
            if child:
                child_agent = MinionAgent(child, self.tool_manager)
                return await child_agent.process_task(task)
            else:
                raise ValueError("No agent can handle this task")
                
        # Process the task
        try:
            # Get available tools
            tools = self.tool_manager.get_available_tools(self.minion.capabilities)
            
            # Update state
            self.minion.state.context.update({
                "task": task.model_dump(),
                "available_tools": [t.name for t in tools.values()]
            })
            
            # Execute tools based on capabilities
            results = {}
            for tool in tools.values():
                if any(cap in task.requires_capabilities for cap in self.minion.capabilities):
                    result = await self.tool_manager.execute_tool(
                        tool.name,
                        self.minion.capabilities,
                        context=task.context
                    )
                    results[tool.name] = result
                    
            return {
                "task_id": task.id,
                "agent_id": self.minion.id,
                "results": results,
                "state": self.minion.state.model_dump()
            }
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {str(e)}")
            raise
        finally:
            # Cleanup
            if task.id in self.tasks:
                del self.tasks[task.id]
