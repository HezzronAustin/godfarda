from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean, create_engine
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional
import logging
from src.storage.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String(50), unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    last_active = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    
    def __repr__(self):
        return f"<User(telegram_id='{self.telegram_id}', username='{self.username}')>"

class Conversation(Base, TimestampMixin):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_time = Column(DateTime, default=func.now())
    last_message_time = Column(DateTime, default=func.now(), onupdate=func.now())
    settings = Column(JSON)  # Renamed from metadata
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"

class Message(Base, TimestampMixin):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('conversations.id'))
    role = Column(String(20))  # 'user' or 'assistant'
    content = Column(Text)
    message_data = Column(JSON)  # Renamed from metadata
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message(role='{self.role}', content='{self.content[:50]}...')>"

def init_db(database_url: str = "sqlite:///godfarda.db") -> None:
    """Initialize the database and create all tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """Create a new database session"""
    Session = sessionmaker(bind=engine)
    return Session()

# Context manager for database sessions
from contextlib import contextmanager

@contextmanager
def session_scope(engine):
    """Provide a transactional scope around a series of operations."""
    session = get_session(engine)
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
