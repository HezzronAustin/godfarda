from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain.schema import BaseMessage
from .models import Agent, Tool, Function
from .factory import DynamicAgent

class AgentRegistry:
    """Registry for managing and creating dynamic agents"""
    
    def __init__(self, session: Session, llm: Any):
        self.session = session
        self.llm = llm
        self.active_agents: Dict[str, DynamicAgent] = {}
    
    def register_agent(self, 
                      name: str,
                      description: str,
                      system_prompt: str,
                      input_schema: Dict[str, Any],
                      output_schema: Dict[str, Any],
                      tools: List[str] = None,
                      functions: List[str] = None,
                      fallback_agent: str = None,
                      metadata: Dict[str, Any] = None) -> Agent:
        """Register a new agent definition"""
        # Create new agent
        agent = Agent(
            name=name,
            description=description,
            system_prompt=system_prompt,
            input_schema=input_schema,
            output_schema=output_schema,
            metadata=metadata or {}
        )
        
        # Add tools if specified
        if tools:
            tool_objs = self.session.query(Tool).filter(Tool.name.in_(tools)).all()
            agent.tools.extend(tool_objs)
        
        # Add functions if specified
        if functions:
            func_objs = self.session.query(Function).filter(Function.name.in_(functions)).all()
            agent.functions.extend(func_objs)
        
        # Set fallback agent if specified
        if fallback_agent:
            fallback = self.session.query(Agent).filter_by(name=fallback_agent).first()
            if fallback:
                agent.fallback_agent_id = fallback.id
        
        self.session.add(agent)
        self.session.commit()
        
        return agent
    
    def register_tool(self,
                     name: str,
                     description: str,
                     function_name: str,
                     input_schema: Dict[str, Any],
                     output_schema: Dict[str, Any],
                     is_async: bool = True,
                     metadata: Dict[str, Any] = None) -> Tool:
        """Register a new tool definition"""
        tool = Tool(
            name=name,
            description=description,
            function_name=function_name,
            input_schema=input_schema,
            output_schema=output_schema,
            is_async=is_async,
            metadata=metadata or {}
        )
        
        self.session.add(tool)
        self.session.commit()
        
        return tool
    
    def register_function(self,
                         name: str,
                         description: str,
                         python_code: str,
                         input_schema: Dict[str, Any],
                         output_schema: Dict[str, Any],
                         is_async: bool = True,
                         metadata: Dict[str, Any] = None) -> Function:
        """Register a new function definition"""
        function = Function(
            name=name,
            description=description,
            python_code=python_code,
            input_schema=input_schema,
            output_schema=output_schema,
            is_async=is_async,
            metadata=metadata or {}
        )
        
        self.session.add(function)
        self.session.commit()
        
        return function
    
    async def get_handler(self,
                         messages: List[BaseMessage],
                         conversation_id: str) -> Optional[DynamicAgent]:
        """Find the most appropriate agent to handle the messages"""
        # Get all active agents
        agents = self.session.query(Agent).filter_by(is_active=True).all()
        
        for agent_def in agents:
            # Create or get cached agent instance
            if agent_def.id not in self.active_agents:
                self.active_agents[agent_def.id] = DynamicAgent(
                    agent_def,
                    self.llm,
                    self.session
                )
            
            agent = self.active_agents[agent_def.id]
            
            # Check if agent can handle messages
            if await agent.can_handle(messages, conversation_id):
                return agent
        
        return None
    
    async def process(self,
                     message: str,
                     conversation_id: str,
                     chat_history: Optional[List[BaseMessage]] = None) -> str:
        """Process a message using the most appropriate agent"""
        # Initialize or use existing chat history
        if chat_history is None:
            chat_history = []
        
        # Add new message to history
        chat_history.append(HumanMessage(content=message))
        
        # Find appropriate handler
        handler = await self.get_handler(chat_history, conversation_id)
        
        if handler is None:
            response = "I'm not sure how to help with that request."
        else:
            response = await handler.process(chat_history, conversation_id)
        
        # Add response to history
        chat_history.append(AIMessage(content=response))
        
        return response
    
    def clear_cache(self):
        """Clear the cached agent instances"""
        self.active_agents.clear()
