from typing import List
import logging
from sqlalchemy.orm import Session
from src.agents.models import Agent, Tool, Role

logger = logging.getLogger(__name__)

DEFAULT_AGENTS = [
    {
        "name": "conversation",
        "description": "General conversation agent that can engage in natural dialogue",
        "system_prompt": """You are a helpful AI assistant. You engage in natural conversations while being:
        1. Helpful and informative
        2. Direct and concise
        3. Professional but friendly
        Always aim to provide accurate information and admit when you're not sure about something.""",
        "agent_type": "chat",
        "agent_role": "assistant",
        "config_data": {
            "llm": {
                "model": "llama3.2:3b",
                "temperature": 0.7,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "context_window": 4096,
                "timeout": 120,
                "streaming": True,
                "max_tokens": 1000,
                "stop_sequences": ["User:", "Assistant:"]
            },
            "output": {
                "format": "text",
                "requires_structured_output": False,
                "max_length": 2000,
                "include_metadata": True
            },
            "memory": {
                "type": "conversation_buffer",
                "max_history": 10,
                "include_system": True
            },
            "tools": {
                "max_iterations": 3,
                "timeout_per_tool": 30,
                "allow_recursive": False,
                "execution_mode": "async"
            },
            "behavior": {
                "role": "assistant",
                "style": "helpful",
                "language": "en",
                "max_depth": 3,
                "error_handling": "graceful"
            },
            "execution": {
                "retry_attempts": 2,
                "retry_delay": 1,
                "timeout": 300
            },
            "monitoring": {
                "log_level": "INFO",
                "track_metrics": True,
                "track_tokens": True,
                "track_latency": True
            }
        }
    },
    {
        "name": "researcher",
        "description": "Research agent that excels at information gathering and analysis",
        "system_prompt": """You are a research assistant AI. Your primary functions are:
        1. Information gathering and verification
        2. Data analysis and synthesis
        3. Providing well-sourced, factual responses
        Always cite sources and explain your reasoning process.""",
        "agent_type": "researcher",
        "agent_role": "researcher",
        "config_data": {
            "llm": {
                "model": "llama3.2:3b",
                "temperature": 0.3,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
                "context_window": 8192,
                "timeout": 180,
                "streaming": True,
                "max_tokens": 2000,
                "stop_sequences": []
            },
            "output": {
                "format": "json",
                "requires_structured_output": True,
                "max_length": 4000,
                "include_metadata": True
            },
            "memory": {
                "type": "conversation_buffer",
                "max_history": 15,
                "include_system": True
            },
            "tools": {
                "max_iterations": 5,
                "timeout_per_tool": 60,
                "allow_recursive": True,
                "execution_mode": "async"
            },
            "behavior": {
                "role": "researcher",
                "style": "academic",
                "language": "en",
                "max_depth": 5,
                "error_handling": "strict"
            },
            "execution": {
                "retry_attempts": 3,
                "retry_delay": 2,
                "timeout": 600
            },
            "monitoring": {
                "log_level": "DEBUG",
                "track_metrics": True,
                "track_tokens": True,
                "track_latency": True
            }
        }
    }
]

DEFAULT_ROLES = [
    {
        "name": "user",
        "description": "End user of the system"
    },
    {
        "name": "assistant",
        "description": "AI assistant responding to user queries"
    },
    {
        "name": "system",
        "description": "System messages and prompts"
    }
]

def seed_roles(session: Session) -> List[Role]:
    """Seed default roles into the database"""
    roles = []
    for role_data in DEFAULT_ROLES:
        # Check if role already exists
        role = session.query(Role).filter_by(name=role_data["name"]).first()
        if not role:
            role = Role(**role_data)
            session.add(role)
            logger.info(f"Created role: {role_data['name']}")
        roles.append(role)
    session.commit()
    return roles

def seed_agents(session: Session) -> List[Agent]:
    """Seed default agents into the database"""
    agents = []
    for agent_data in DEFAULT_AGENTS:
        # Check if agent already exists
        agent = session.query(Agent).filter_by(name=agent_data["name"]).first()
        if not agent:
            agent = Agent(**agent_data)
            session.add(agent)
            logger.info(f"Created agent: {agent_data['name']}")
        agents.append(agent)
    session.commit()
    return agents

def seed_default_tools(session: Session, agents: List[Agent]):
    """Seed default tools for agents"""
    for agent in agents:
        if agent.name == "researcher":
            # Add research-specific tools
            tools = [
                {
                    "name": "search",
                    "description": "Search the internet for information",
                    "tool_type": "langchain",
                    "implementation": """
def search(query: str, **kwargs):
    \"\"\"Search the internet for information\"\"\"
    # Implementation would go here
    pass
                    """,
                    "parameters": {
                        "query": {"type": "string", "description": "Search query"}
                    }
                },
                {
                    "name": "analyze",
                    "description": "Analyze and summarize text",
                    "tool_type": "langchain",
                    "implementation": """
def analyze(text: str, **kwargs):
    \"\"\"Analyze and summarize text\"\"\"
    # Implementation would go here
    pass
                    """,
                    "parameters": {
                        "text": {"type": "string", "description": "Text to analyze"}
                    }
                }
            ]
            
            for tool_data in tools:
                # Check if tool already exists
                tool = session.query(Tool).filter_by(
                    name=tool_data["name"],
                    agent_id=agent.id
                ).first()
                
                if not tool:
                    tool = Tool(**tool_data, agent_id=agent.id)
                    session.add(tool)
                    logger.info(f"Created tool: {tool_data['name']} for agent: {agent.name}")
    
    session.commit()

def seed_all(session: Session):
    """Seed all default data"""
    logger.info("Starting database seeding...")
    
    try:
        # Seed in correct order for foreign key constraints
        roles = seed_roles(session)
        agents = seed_agents(session)
        seed_default_tools(session, agents)
        
        logger.info("Database seeding completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database seeding: {str(e)}")
        session.rollback()
        raise
