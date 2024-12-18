from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from src.agents.models import Agent, Tool, Function, AgentExecution
from src.agents.factory import DynamicAgent
from langchain.chat_models import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage

class AgentRegistry:
    def __init__(self, session: Session, llm: Optional[Any] = None):
        self.session = session
        self.llm = llm or ChatOpenAI()
        self._agents: Dict[str, DynamicAgent] = {}
        
    def register_agent(self, agent_def: Agent) -> DynamicAgent:
        """Register a new agent from its database definition"""
        if agent_def.name in self._agents:
            return self._agents[agent_def.name]
            
        agent = DynamicAgent(
            agent_def=agent_def,
            llm=self.llm,
            session=self.session
        )
        self._agents[agent_def.name] = agent
        return agent
        
    def get_agent(self, name: str) -> Optional[DynamicAgent]:
        """Get a registered agent by name"""
        if name in self._agents:
            return self._agents[name]
            
        # Try loading from database
        agent_def = self.session.query(Agent).filter(Agent.name == name).first()
        if agent_def:
            return self.register_agent(agent_def)
        return None
        
    async def get_handler(self, messages: List[BaseMessage], conversation_id: str) -> Optional[DynamicAgent]:
        """Find the most appropriate agent to handle the messages"""
        # Get all active agents from database
        agents = self.session.query(Agent).all()
        
        for agent_def in agents:
            # Create or get cached agent instance
            agent = self.get_agent(agent_def.name)
            if agent and await agent.can_handle(messages, conversation_id):
                return agent
                
        return None
        
    async def process(self, messages: List[BaseMessage], conversation_id: str) -> Dict[str, Any]:
        """Process messages using the most appropriate agent"""
        handler = await self.get_handler(messages, conversation_id)
        if not handler:
            return {"response": "I'm not sure how to help with that request.", "agent": None}
            
        try:
            # Create execution record
            execution = AgentExecution(
                agent_id=handler.agent_def.id,
                input_data={'messages': [str(m.content) for m in messages]},
                status='in_progress'
            )
            self.session.add(execution)
            self.session.commit()
            
            # Process message
            result = await handler.process_message(messages[-1].content)
            
            # Update execution record
            execution.status = 'success'
            execution.output_data = result
            execution.execution_metadata = {
                'agent_name': handler.name,
                'conversation_id': conversation_id,
                'message_count': len(messages)
            }
            self.session.commit()
            
            return {"response": result, "agent": handler.name}
            
        except Exception as e:
            if 'execution' in locals():
                execution.status = 'failure'
                execution.error_message = str(e)
                execution.execution_metadata = {
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                }
                self.session.commit()
            raise
        
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        return list(self._agents.keys())
