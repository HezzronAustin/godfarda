from sqlalchemy import Column, Integer, String, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.storage.base import Base, TimestampMixin

class Agent(Base, TimestampMixin):
    __tablename__ = 'agents'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    system_prompt = Column(Text)
    config_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    max_chain_depth = Column(Integer, default=3)
    chain_strategy = Column(String(50), default='sequential')
    temperature = Column(Integer, default=0.7)
    
    # Relationships
    functions = relationship("Function", back_populates="agent")
    tools = relationship("Tool", back_populates="agent")
    executions = relationship("AgentExecution", back_populates="agent")

class Function(Base, TimestampMixin):
    __tablename__ = 'functions'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parameters = Column(JSON)
    implementation = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="functions")

class Tool(Base, TimestampMixin):
    __tablename__ = 'tools'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    config_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="tools")

class AgentExecution(Base, TimestampMixin):
    __tablename__ = 'agent_executions'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(Integer, ForeignKey('agents.id'))
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_data = Column(JSON)  # Renamed from metadata
    status = Column(String(50))  # 'started', 'completed', 'failed'
    error_message = Column(Text)
    
    # Relationships
    agent = relationship("Agent", back_populates="executions")
    conversation = relationship("Conversation", backref="agent_executions")
