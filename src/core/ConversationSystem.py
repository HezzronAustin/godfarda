from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models.ollama import ChatOllama
from langchain.tools import Tool

from src.agents.factory import DynamicAgent
from src.agents.registry import AgentRegistry
from src.storage.database import session_scope
from src.agents.models import Agent, User, Conversation, Message
from langchain_core.messages import SystemMessage
from langchain.schema import AIMessage, HumanMessage
from typing import List
import logging
import time
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MessageData:
    role: str
    content: str
    timestamp: str = field(default=None)


class ConversationSystem:
    def __init__(self, engine):
        """Initialize the conversation system with necessary components."""
        try:
            start_time = time.time()
            logger.info("Initializing Conversation system")

            # Store engine for session management
            self.engine = engine

            # Initialize Ollama LLM
            self.llm = ChatOllama(
                model="llama3.2:3b",
                temperature=0,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=False,
                context_window=4096,
                timeout=120,
                base_url=os.getenv('OLLAMA_BASE_URL')
            )

            logger.debug("LLM initialized")

            # Initialize agent registry and function store
            self.agent_registry = AgentRegistry(engine)
            tools = []
            with session_scope(self.engine) as session:
                agents = session.query(Agent).filter_by(is_active=True).all()
                for agent in agents:
                    logger.debug(f"Loading agent: {agent.name}")
                    # Define tools for the LangChain agent
                    agent_tool = Tool(
                        name=agent.name,
                        func=DynamicAgent(agent, self.llm, session).process_message,
                        description=agent.description
                    )
                    tools.append(agent_tool)

            # Initialize LangChain memory and agent
            self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=self.memory
            )

            logger.info(f"Conversation system initialized in {time.time() - start_time:.2f}s")

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

    async def converse(self, message: str, user_id: str) -> str:
        """Process a message and return a response."""
        try:
            with session_scope(self.engine) as session:
                # Get or create user
                user = session.query(User).filter_by(telegram_id=user_id).first()
                if not user:
                    user = User(telegram_id=user_id)
                    session.add(user)
                    session.flush()

                # Get or create active conversation
                conversation = (
                    session.query(Conversation)
                    .filter_by(user_id=user.id, is_active=True)
                    .first()
                )

                if not conversation:
                    conversation = Conversation(user_id=user.id)
                    session.add(conversation)
                    session.flush()

                # Add user message to database
                user_message = Message(
                    conversation_id=conversation.id,
                    role='user',
                    content=message
                )
                session.add(user_message)

                # Get recent conversation history (last 5 messages)
                recent_messages = (
                    session.query(Message)
                    .filter_by(conversation_id=conversation.id)
                    .order_by(Message.created_at.desc())
                    .limit(5)
                    .all()
                )

                # Update LangChain memory with history
                for msg in reversed(recent_messages):
                    role = "user" if msg.role == "user" else "assistant"
                    self.memory.chat_memory.add_message(
                        HumanMessage(content=msg.content) if role == "user" else AIMessage(content=msg.content))

                # Use LangChain agent to process the message
                response = self.agent.run(message)

                # Add assistant message to database
                assistant_message = Message(
                    conversation_id=conversation.id,
                    role='assistant',
                    content=response
                )
                session.add(assistant_message)

                return response

        except Exception as e:
            logger.error(f"Error in LangChain conversation: {str(e)}", exc_info=True)
            return "Sorry, I encountered an error while processing your request."

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
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.created_at
                    )
                    for msg in messages
                ]

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
            raise
