from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Float, DateTime, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.storage.base import Base, TimestampMixin
from typing import Dict, Any, List, Optional
from datetime import datetime

# Association tables
agent_tool_association = Table(
    'agent_tool_association',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id')),
    Column('tool_id', Integer, ForeignKey('tools.id'))
)

agent_function_association = Table(
    'agent_function_association',
    Base.metadata,
    Column('agent_id', Integer, ForeignKey('agents.id')),
    Column('function_id', Integer, ForeignKey('functions.id'))
)

class Agent(Base, TimestampMixin):
    """Agent definition stored in database"""
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    system_prompt = Column(String, nullable=False)
    input_schema = Column(JSON)  # JSON Schema for expected input
    output_schema = Column(JSON)  # JSON Schema for expected output
    config_data = Column(JSON)  # Configuration data
    is_active = Column(Boolean, default=True)
    max_chain_depth = Column(Integer, default=3)
    chain_strategy = Column(String, default='sequential')
    
    # LLM Configuration
    llm_provider = Column(String, default='ollama')  # ollama, openai, anthropic, etc.
    llm_model = Column(String, default='mistral')    # model name
    llm_config = Column(JSON, default={              # Provider-specific configuration
        'temperature': 0.7,
        'top_p': 1.0,
        'presence_penalty': 0.0,
        'frequency_penalty': 0.0,
        'repeat_penalty': 1.1,
        'context_window': 4096,
        'timeout': 120,
        'streaming': True,
        'format': None  # Can be 'json' for structured output
    })
    
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    presence_penalty = Column(Float, default=0.0)
    frequency_penalty = Column(Float, default=0.0)
    fallback_agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    
    tools = relationship("Tool", secondary=agent_tool_association, back_populates="agent")
    functions = relationship("Function", secondary=agent_function_association, back_populates="agent")
    executions = relationship("AgentExecution", back_populates="agent")
    fallback_agent = relationship("Agent", remote_side=[id])

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'system_prompt': self.system_prompt,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'tools': [tool.to_dict() for tool in self.tools],
            'functions': [func.to_dict() for func in self.functions],
            'config_data': self.config_data,
            'llm_config': {
                'provider': self.llm_provider,
                'model': self.llm_model,
                'config': self.llm_config,
                'temperature': self.temperature,
                'top_p': self.top_p,
                'presence_penalty': self.presence_penalty,
                'frequency_penalty': self.frequency_penalty
            },
            'chain_config': {
                'max_depth': self.max_chain_depth,
                'strategy': self.chain_strategy
            }
        }

class Tool(Base, TimestampMixin):
    """Tool definition stored in database"""
    __tablename__ = 'tools'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    function_name = Column(String)  # Python function to call
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    is_async = Column(Boolean, default=True)
    config_data = Column(JSON)  # Tool configuration
    agent_id = Column(Integer, ForeignKey('agents.id'))
    
    agent = relationship("Agent", back_populates="tools")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'function_name': self.function_name,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'is_async': self.is_async,
            'config_data': self.config_data
        }

class Function(Base, TimestampMixin):
    """Function definition stored in database"""
    __tablename__ = 'functions'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    python_code = Column(String, nullable=False)  # Actual Python code as string
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    is_async = Column(Boolean, default=True)
    config_data = Column(JSON)  # Function configuration
    agent_id = Column(Integer, ForeignKey('agents.id'))
    
    agent = relationship("Agent", back_populates="functions")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'is_async': self.is_async,
            'config_data': self.config_data
        }

class AgentExecution(Base, TimestampMixin):
    """Record of agent executions"""
    __tablename__ = 'agent_executions'

    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    conversation_id = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_time = Column(Float)  # in seconds
    chain_depth = Column(Integer, default=0)
    parent_execution_id = Column(Integer, ForeignKey('agent_executions.id'), nullable=True)
    status = Column(String)  # success, failure, in_progress
    error_message = Column(String, nullable=True)
    execution_metadata = Column(JSON)  # Additional execution details
    
    agent = relationship("Agent", back_populates="executions")
