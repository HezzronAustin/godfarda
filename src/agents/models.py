from sqlalchemy import Column, Integer, String, JSON, Boolean, ForeignKey, Text, DateTime, UUID, Float
from sqlalchemy.orm import relationship
from src.storage.base import Base, TimestampMixin
import uuid
from datetime import datetime

class Agent(Base, TimestampMixin):
    __tablename__ = 'agents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    system_prompt = Column(Text)
    agent_type = Column(String(50))
    agent_status = Column(String(20), default='Active')
    version = Column(String(20), default='1.0')
    agent_role = Column(String(50))
    execution_frequency = Column(String(50), default='On-Demand')
    response_time = Column(String(50))
    last_executed_by = Column(String(100))
    error_count = Column(Integer, default=0)
    config_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    max_chain_depth = Column(Integer, default=3)
    chain_strategy = Column(String(50), default='sequential')
    temperature = Column(Float, default=0.7)
    
    # Relationships
    tools = relationship("Tool", back_populates="agent")
    executions = relationship("AgentExecution", back_populates="agent")

    def __repr__(self):
        return f"<Agent(name='{self.name}', type='{self.agent_type}', status='{self.agent_status}')>"

class Tool(Base, TimestampMixin):
    __tablename__ = 'tools'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    config_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    agent = relationship("Agent", back_populates="tools")

class AgentExecution(Base, TimestampMixin):
    __tablename__ = 'agent_executions'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('agents.id'))
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_data = Column(JSON)  # Renamed from metadata
    status = Column(String(50))  # 'started', 'completed', 'failed'
    error_message = Column(Text)
    is_vectorized = Column(Boolean, default=False)  # New flag for tracking vectorization status
    vectorized_at = Column(DateTime)  # New column to track when it was vectorized
    
    # Relationships
    agent = relationship("Agent", back_populates="executions")
    conversation = relationship("Conversation", back_populates="agent_executions")

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(100), unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")

    def __repr__(self):
        return f"<User(telegram_id='{self.telegram_id}', username='{self.username}')>"

class Conversation(Base, TimestampMixin):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String(200))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    agent_executions = relationship("AgentExecution", back_populates="conversation")

    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

class Message(Base, TimestampMixin):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    message_metadata = Column(JSON)  # Renamed from metadata to avoid SQLAlchemy conflict
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(conversation_id={self.conversation_id}, role='{self.role}')>"
