from sqlalchemy import Engine
from sqlalchemy.orm import Session
from src.agents.models import Agent
from src.storage.database import session_scope
import logging

logger = logging.getLogger('agents.registry')

class AgentRegistry:
    def __init__(self, engine: Engine):
        self.engine = engine
        
    def get_agent(self, name: str) -> Agent:
        """Get an agent by name"""
        with session_scope(self.engine) as session:
            agent = session.query(Agent).filter_by(name=name, is_active=True).first()
            if not agent:
                raise ValueError(f"Agent {name} not found or not active")
            return agent
            
    def register_agent(self, agent: Agent) -> None:
        """Register a new agent"""
        with session_scope(self.engine) as session:
            existing = session.query(Agent).filter_by(name=agent.name).first()
            if existing:
                raise ValueError(f"Agent {agent.name} already exists")
            session.add(agent)
            
    def list_agents(self) -> list[Agent]:
        """List all active agents"""
        with session_scope(self.engine) as session:
            return session.query(Agent).filter_by(is_active=True).all()
