from src.storage.base import Base
from src.agents.models import Agent, Tool, Function, AgentExecution
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging

def init_agent_db(engine):
    """Initialize the agent database tables and create default agents"""
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if we need to create default agents
        if session.query(Agent).count() == 0:
            # Create default RAG agent
            rag_agent = Agent(
                name="RAGAgent",
                description="Default RAG system agent for answering questions",
                system_prompt="""You are a helpful assistant that uses retrieved context to answer questions accurately.
                Always base your answers on the provided context and acknowledge when you don't have enough information.""",
                config_data={
                    "type": "rag",
                    "capabilities": ["question_answering", "information_retrieval"]
                },
                is_active=True,
                max_chain_depth=3,
                chain_strategy="sequential",
                temperature=0.7
            )
            session.add(rag_agent)
            
            # Create default function agent
            function_agent = Agent(
                name="FunctionAgent",
                description="Agent for executing and managing functions",
                system_prompt="""You are a function execution agent. Your role is to:
                1. Execute functions safely and efficiently
                2. Handle function parameters appropriately
                3. Return results in a structured format""",
                config_data={
                    "type": "function",
                    "capabilities": ["function_execution", "parameter_handling"]
                },
                is_active=True,
                max_chain_depth=2,
                chain_strategy="sequential",
                temperature=0.5
            )
            session.add(function_agent)
            
            # Commit the changes
            session.commit()
            logging.info("Created default agents")
            
    except Exception as e:
        logging.error(f"Error initializing agent database: {str(e)}")
        raise
    finally:
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    # This is just for testing - in production the engine should be passed in
    engine = create_engine("sqlite:///test.db")
    init_agent_db(engine)
