from sqlalchemy import Column, Integer, String, JSON, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from typing import Dict, Any, List, Optional
from datetime import datetime

Base = declarative_base()

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

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(String, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, default=lambda: datetime.utcnow().isoformat(), onupdate=lambda: datetime.utcnow().isoformat())

class Agent(Base, TimestampMixin):
    """Agent definition stored in database"""
    __tablename__ = 'agents'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    system_prompt = Column(String)
    input_schema = Column(JSON)  # JSON Schema for expected input
    output_schema = Column(JSON)  # JSON Schema for expected output
    tools = relationship("Tool", secondary=agent_tool_association)
    functions = relationship("Function", secondary=agent_function_association)
    fallback_agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)
    
    # Chain-specific fields
    max_chain_depth = Column(Integer, default=3)  # Maximum recursion depth
    chain_strategy = Column(String, default='sequential')  # sequential, parallel, etc.
    
    # Prompt engineering fields
    temperature = Column(Float, default=0.7)
    top_p = Column(Float, default=1.0)
    presence_penalty = Column(Float, default=0.0)
    frequency_penalty = Column(Float, default=0.0)
    
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
            'metadata': self.metadata,
            'chain_config': {
                'max_depth': self.max_chain_depth,
                'strategy': self.chain_strategy
            }
        }

class Tool(Base, TimestampMixin):
    """Tool definition stored in database"""
    __tablename__ = 'tools'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    function_name = Column(String)  # Python function to call
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    is_async = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'function_name': self.function_name,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'is_async': self.is_async,
            'metadata': self.metadata
        }

class Function(Base, TimestampMixin):
    """Function definition stored in database"""
    __tablename__ = 'functions'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    description = Column(String)
    python_code = Column(String)  # Actual Python code as string
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    is_async = Column(Boolean, default=True)
    metadata = Column(JSON, default=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'is_async': self.is_async,
            'metadata': self.metadata
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
    metadata = Column(JSON, default=dict)
