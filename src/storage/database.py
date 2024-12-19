from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from contextlib import contextmanager
from src.agents.models import Base, User, Conversation, Message, Agent, Tool, AgentExecution
import logging
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///godfarda.db')

def init_db(database_url: str = DATABASE_URL) -> None:
    """Initialize the database and create all tables"""
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """Create a new database session"""
    Session = sessionmaker(bind=engine)
    return Session()

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
