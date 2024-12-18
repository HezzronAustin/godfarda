from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from src.agents.models import Agent, Tool, Function, AgentExecution
from src.agents.factory import DynamicAgent
from langchain.chat_models import ChatOpenAI, ChatOllama, ChatAnthropic
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import logging

logger = logging.getLogger('agents.registry')

class AgentRegistry:
    def __init__(self, session: Session, default_llm: Optional[Any] = None):
        logger.info("Initializing AgentRegistry")
        self.session = session
        self.default_llm = default_llm
        self._agents: Dict[str, DynamicAgent] = {}
        
    def _create_llm(self, agent_def: Agent) -> Any:
        """Create LLM instance based on agent configuration"""
        provider = agent_def.llm_provider.lower()
        config = agent_def.llm_config or {}
        
        try:
            if provider == 'ollama':
                return ChatOllama(
                    model=agent_def.llm_model,
                    temperature=agent_def.temperature,
                    top_p=agent_def.top_p,
                    **config
                )
            elif provider == 'openai':
                return ChatOpenAI(
                    model=agent_def.llm_model,
                    temperature=agent_def.temperature,
                    top_p=agent_def.top_p,
                    presence_penalty=agent_def.presence_penalty,
                    frequency_penalty=agent_def.frequency_penalty,
                    **config
                )
            elif provider == 'anthropic':
                return ChatAnthropic(
                    model=agent_def.llm_model,
                    temperature=agent_def.temperature,
                    **config
                )
            else:
                logger.warning(f"Unknown LLM provider: {provider}, using default LLM")
                return self.default_llm
                
        except Exception as e:
            logger.error(f"Error creating LLM for provider {provider}: {str(e)}", exc_info=True)
            if self.default_llm:
                logger.info("Falling back to default LLM")
                return self.default_llm
            raise
        
    def register_agent(self, agent_def: Agent) -> DynamicAgent:
        """Register a new agent from its database definition"""
        logger.info(f"Registering agent: {agent_def.name}")
        
        if agent_def.name in self._agents:
            logger.debug(f"Agent {agent_def.name} already registered, returning existing instance")
            return self._agents[agent_def.name]
            
        try:
            # Create LLM instance for this agent
            llm = self._create_llm(agent_def)
            
            agent = DynamicAgent(
                agent_def=agent_def,
                llm=llm,
                session=self.session
            )
            self._agents[agent_def.name] = agent
            logger.info(f"Successfully registered agent: {agent_def.name}")
            return agent
        except Exception as e:
            logger.error(f"Error registering agent {agent_def.name}: {str(e)}", exc_info=True)
            raise
        
    def get_agent(self, name: str) -> Optional[DynamicAgent]:
        """Get a registered agent by name"""
        logger.debug(f"Getting agent: {name}")
        
        if name in self._agents:
            logger.debug(f"Found cached agent: {name}")
            return self._agents[name]
            
        try:
            # Try loading from database
            agent_def = self.session.query(Agent).filter(Agent.name == name).first()
            if agent_def:
                logger.debug(f"Found agent {name} in database, registering")
                return self.register_agent(agent_def)
            
            logger.warning(f"Agent {name} not found")
            return None
        except Exception as e:
            logger.error(f"Error getting agent {name}: {str(e)}", exc_info=True)
            raise
        
    async def get_handler(self, messages: List[BaseMessage], conversation_id: str) -> Optional[DynamicAgent]:
        """Find the most appropriate agent to handle the messages"""
        logger.debug(f"Finding handler for conversation: {conversation_id}")
        
        try:
            # Get all active agents from database
            agents = self.session.query(Agent).all()
            logger.debug(f"Found {len(agents)} potential handlers")
            
            for agent_def in agents:
                # Create or get cached agent instance
                agent = self.get_agent(agent_def.name)
                if agent:
                    logger.debug(f"Checking if agent {agent.name} can handle the messages")
                    if await agent.can_handle(messages, conversation_id):
                        logger.info(f"Agent {agent.name} will handle the messages")
                        return agent
            
            logger.info("No suitable handler found for the messages")
            return None
            
        except Exception as e:
            logger.error(f"Error finding handler: {str(e)}", exc_info=True)
            raise
        
    async def process(self, messages: List[BaseMessage], conversation_id: str) -> Dict[str, Any]:
        """Process messages using the most appropriate agent"""
        logger.info(f"Processing messages for conversation: {conversation_id}")
        
        try:
            handler = await self.get_handler(messages, conversation_id)
            if not handler:
                logger.warning("No handler found, returning default response")
                return {"response": "I'm not sure how to help with that request.", "agent": None}
            
            # Create execution record
            execution = AgentExecution(
                agent_id=handler.agent_def.id,
                input_data={'messages': [str(m.content) for m in messages]},
                status='in_progress'
            )
            self.session.add(execution)
            self.session.commit()
            logger.debug(f"Created execution record for agent {handler.name}")
            
            try:
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
                
                logger.info(f"Successfully processed messages with agent {handler.name}")
                return {"response": result, "agent": handler.name}
                
            except Exception as e:
                logger.error(f"Error processing messages with agent {handler.name}: {str(e)}", exc_info=True)
                execution.status = 'failure'
                execution.error_message = str(e)
                execution.execution_metadata = {
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                }
                self.session.commit()
                raise
                
        except Exception as e:
            logger.error(f"Error in process: {str(e)}", exc_info=True)
            raise
        
    def list_agents(self) -> List[str]:
        """List all registered agent names"""
        agent_names = list(self._agents.keys())
        logger.debug(f"Listed {len(agent_names)} registered agents")
        return agent_names
