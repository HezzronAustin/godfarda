from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey, Float, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json
import os
import logging

Base = declarative_base()

class Conversation(Base):
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(String)
    context = Column(JSON)
    response = Column(String)
    meta_data = Column(JSON)
    
    # Relationship
    user = relationship("User", back_populates="conversations")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")

class AgentState(Base):
    __tablename__ = 'agent_states'
    
    id = Column(Integer, primary_key=True)
    agent_id = Column(String)
    state = Column(JSON)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True)
    content = Column(Text)  # Using Text for longer content
    meta_data = Column(JSON)
    embedding_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db(db_path: str = "sqlite:///godfarda.db"):
    """Initialize the database and create all tables."""
    try:
        engine = create_engine(db_path)
        # Drop all tables first to ensure clean slate
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        logging.info(f"Database initialized successfully at {db_path}")
        return engine
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise

def get_session(engine):
    """Create a new database session."""
    Session = sessionmaker(bind=engine)
    return Session()
