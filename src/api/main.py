from fastapi import FastAPI, HTTPException, Header
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..core.config import settings
from ..core.registry import registry
from ..core.utils import ToolException

app = FastAPI(
    title="AI Tools Ecosystem API",
    version=settings.API_VERSION,
    docs_url=f"{settings.API_PREFIX}/docs"
)

class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class AgentRequest(BaseModel):
    agent_name: str
    input_data: Dict[str, Any]

async def verify_api_key(api_key: Optional[str] = Header(None)) -> None:
    """Verify API key if required."""
    if settings.REQUIRE_API_KEY:
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
        # Add your API key validation logic here

@app.post(f"{settings.API_PREFIX}/tools/{{tool_name}}")
async def execute_tool(
    tool_name: str,
    request: ToolRequest,
    api_key: Optional[str] = Header(None)
):
    """Execute a specific tool with given parameters."""
    await verify_api_key(api_key)
    
    try:
        tool_class = registry.get_tool(tool_name)
        if not tool_class:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        tool = tool_class()
        response = await tool.execute(request.parameters)
        return response
        
    except ToolException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post(f"{settings.API_PREFIX}/agents/{{agent_name}}")
async def process_agent(
    agent_name: str,
    request: AgentRequest,
    api_key: Optional[str] = Header(None)
):
    """Process data using a specific agent."""
    await verify_api_key(api_key)
    
    try:
        agent_class = registry.get_agent(agent_name)
        if not agent_class:
            raise HTTPException(status_code=404, detail=f"Agent {agent_name} not found")
        
        # Agent configuration would be loaded from a config store in production
        config = {"name": agent_name, "allowed_tools": []}
        agent = agent_class(config)
        
        await agent.initialize()
        response = await agent.process(request.input_data)
        return response
        
    except ToolException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get(f"{settings.API_PREFIX}/tools")
async def list_tools(api_key: Optional[str] = Header(None)):
    """List all available tools."""
    await verify_api_key(api_key)
    return {"tools": registry.list_tools()}

@app.get(f"{settings.API_PREFIX}/agents")
async def list_agents(api_key: Optional[str] = Header(None)):
    """List all available agents."""
    await verify_api_key(api_key)
    return {"agents": registry.list_agents()}
