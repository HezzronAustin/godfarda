from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models.ollama import ChatOllama
from langchain.tools import Tool

from src.agents.factory import DynamicAgent
from src.agents.registry import AgentRegistry
from src.storage.database import session_scope, create_engine, sessionmaker
from src.agents.models import Agent, User, Conversation, Message, Role
from langchain_core.messages import SystemMessage
from langchain.schema import AIMessage, HumanMessage
from typing import List
import logging
import time
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv('DATABASE_URL')

@dataclass
class MessageData:
    role: str
    content: str
    timestamp: str = field(default=None)


class ConversationSystem:
    def __init__(self, engine=None):
        """Initialize the conversation system"""
        try:
            start_time = time.time()
            logger.info("Initializing Conversation system")
            
            self.engine = engine or create_engine(DATABASE_URL)
            self.Session = sessionmaker(bind=self.engine)
            session = self.Session()

            # Initialize Ollama LLM
            self.llm = ChatOllama(
                model="llama3.2:3b",
                temperature=0.6,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=False,
                context_window=8192,
                timeout=120
            )

            logger.debug("LLM initialized")

            # Initialize agent registry and function store
            self.agent_registry = AgentRegistry(engine)
            tools = []
            
            # Load active agents as tools
            try:
                agents = session.query(Agent).filter_by(is_active=True).all()
                for agent in agents:
                    logger.debug(f"Loading agent: {agent.name}")
                    with self.Session() as agent_session:
                        dynamic_agent = DynamicAgent(agent, agent_session)
                    
                    async def _process_message(message: str, agent=dynamic_agent) -> str:
                        """Wrapper to handle async process_message"""
                        try:
                            result = await agent.process_message(message)
                            return result.get('response', '')
                        except Exception as e:
                            logger.error(f"Error in agent {agent.name}: {str(e)}", exc_info=True)
                            return f"Error processing message: {str(e)}"
                    
                    # Define tools for the LangChain agent
                    agent_tool = Tool(
                        name=agent.name,
                        func=_process_message,
                        description=agent.description,
                        coroutine=_process_message,
                        return_direct=True
                    )
                    tools.append(agent_tool)
            finally:
                session.close()

            logger.debug(f"Loaded {len(tools)} agent tools")

            # Initialize LangChain memory and agent
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=self.memory,
                max_iterations=10,
                handle_parsing_errors=True
            )

            elapsed_time = time.time() - start_time
            logger.info(f"Conversation system initialized in {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize conversation system: {e}", exc_info=True)
            raise

    def custom_search_function(self, query: str) -> str:
        """Custom search logic."""
        return "Search result placeholder."

    def query_database(self, query: str) -> str:
        """Custom database query logic."""
        with session_scope(self.engine) as session:
            # Implement your custom database query here
            return "Database query result placeholder."

    async def converse(self, message: str, telegram_id: int = None) -> str:
        """Process a message in a conversation"""
        try:
            # Create or get session
            session = self.Session()
            
            try:
                # Get or create user
                user = self.get_or_create_user(session, telegram_id)
                
                # Get or create conversation
                conversation = self.get_or_create_conversation(session, user.id)
                
                # Get roles
                user_role = session.query(Role).filter_by(name='user').first()
                assistant_role = session.query(Role).filter_by(name='assistant').first()
                
                if not user_role or not assistant_role:
                    raise ValueError("Required roles not found in database")
                
                # Add user message to database
                user_message = Message(
                    conversation_id=conversation.id,
                    role_id=user_role.id,
                    content=message
                )
                session.add(user_message)
                session.commit()
                
                # Get chat history
                chat_history = self.get_chat_history(session, conversation.id)
                
                # Use LangChain agent to process the message
                response = await self.agent.ainvoke(
                    {"input": message, "chat_history": chat_history}
                )
                
                # Extract the output from the response
                response_text = response.get("output", "I encountered an error processing your request.")
                
                # Add assistant message to database
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role_id=assistant_role.id,
                    content=response_text
                )
                session.add(assistant_message)
                session.commit()
                
                return response_text
                
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error in LangChain conversation: {str(e)}", exc_info=True)
            raise

    def get_or_create_user(self, session, telegram_id):
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id)
            session.add(user)
            session.flush()  # Get the user ID
        return user

    def get_or_create_conversation(self, session, user_id):
        conversation = (
            session.query(Conversation)
            .filter_by(user_id=user_id, is_active=True)
            .first()
        )
        if not conversation:
            conversation = Conversation(user_id=user_id, is_active=True)
            session.add(conversation)
            session.flush()  # Get the conversation ID
        return conversation

    def get_chat_history(self, session, conversation_id):
        history = session.query(Message).filter_by(
            conversation_id=conversation_id
        ).order_by(Message.created_at.asc()).all()
        
        # Convert to LangChain format
        chat_history = []
        for msg in history:
            if msg.role.name in ['user', 'assistant']:
                chat_history.append(
                    HumanMessage(content=msg.content) if msg.role.name == 'user'
                    else AIMessage(content=msg.content)
                )
        return chat_history

    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[MessageData]:
        """Get conversation history for a user."""
        try:
            with session_scope(self.engine) as session:
                user = session.query(User).filter_by(telegram_id=user_id).first()
                if not user:
                    return []

                conversation = (
                    session.query(Conversation)
                    .filter_by(user_id=user.id, is_active=True)
                    .first()
                )

                if not conversation:
                    return []

                messages = (
                    session.query(Message)
                    .filter_by(conversation_id=conversation.id)
                    .order_by(Message.created_at.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    MessageData(
                        role=msg.role.name,
                        content=msg.content,
                        timestamp=msg.created_at
                    )
                    for msg in messages
                ]

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
            raise
