from uuid import UUID, uuid4
from typing import Dict, Set, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ToolPermission(BaseModel):
    name: str
    description: str
    level: int = Field(ge=0, le=10)
    
class AgentCapability(BaseModel):
    name: str
    description: str
    permissions: Set[str]
    capabilities_required: Set[str] = Field(default_factory=set)
    resource_cost: float = Field(ge=0.0)
    
class AgentState(BaseModel):
    memory: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
class ChainableMinion(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    capabilities: Set[str] = Field(default_factory=set)
    chain_depth: int = Field(default=0, ge=0)
    max_depth: int = Field(default=5, ge=1)
    parent_id: Optional[UUID] = None
    children: Dict[UUID, 'ChainableMinion'] = Field(default_factory=dict)
    execution_chain: List[UUID] = Field(default_factory=list)
    state: AgentState = Field(default_factory=AgentState)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
