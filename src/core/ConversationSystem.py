import asyncio
import os
from datetime import datetime
from pickle import FALSE
from typing import List, Dict, Optional
import logging
import time
from dataclasses import dataclass, field

from langchain_core.messages import SystemMessage
from pydantic import BaseModel
from langchain_community.chat_models.ollama import ChatOllama
from langchain.memory import ChatMessageHistory
from langchain.schema import AIMessage, HumanMessage, BaseMessage
from sqlalchemy import Engine
from sqlalchemy.engine import url

from src.agents.registry import AgentRegistry
from src.agents.function_store import FunctionStore
from src.storage.database import User, Conversation, Message, session_scope

# Configure logging
logger = logging.getLogger('ai.core')

@dataclass
class MessageData:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ConversationSystem:
    def __init__(self, engine: Engine = None):
        """Initialize the conversation system."""
        logger.info("Initializing Conversation system")
        start_time = time.time()

        try:
            self.engine = engine
            # Initialize Ollama LLM
            self.llm = ChatOllama(
                model="llama3.2:3b",
                temperature=0,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=False, # Disable streaming for better response handling
                context_window=4096,
                timeout=120,
                base_url=os.getenv('OLLAMA_BASE_URL')
            )
            
            logger.debug("LLM initialized")
            
            # Initialize agent registry and function store
            self.agent_registry = AgentRegistry(engine)
            self.function_store = FunctionStore()
            
            logger.info(f"Conversation system initialized in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize conversation system: {e}", exc_info=True)
            raise

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
                
                # Build message list with history
                messages = [
                    SystemMessage(content="You are a helpful AI assistant. Provide natural, conversational responses. When asked about the weather, explain that you don't have access to real-time weather data and suggest checking a weather service.")
                ]
                
                # Add conversation history in chronological order
                for msg in reversed(recent_messages):
                    if msg.role == 'user':
                        messages.append(HumanMessage(content=msg.content))
                    else:
                        messages.append(AIMessage(content=msg.content))
                
                # Add current message
                messages.append(HumanMessage(content=message))
                
                try:
                    ai_response = await self.llm.agenerate([messages])
                    if not ai_response or not ai_response.generations:
                        raise ValueError("Empty response from LLM")
                    
                    response_text = ai_response.generations[0][0].text.strip()
                    if not response_text or response_text.isspace():
                        response_text = "I apologize, but I encountered an issue generating a response. Please try asking your question again."
                    
                    logger.info(f"AI Response: {response_text[:100]}...")  # Log first 100 chars
                    
                    # Add assistant message to database
                    assistant_message = Message(
                        conversation_id=conversation.id,
                        role='assistant',
                        content=response_text
                    )
                    session.add(assistant_message)
                    
                    return response_text
                    
                except Exception as e:
                    error_msg = "I apologize, but I encountered an error while processing your message. Please try again."
                    logger.error(f"Error generating response: {str(e)}")
                    return error_msg

        except Exception as e:
            logger.error(f"Error in conversation: {str(e)}", exc_info=True)
            raise

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
                    .order_by(Message.created_at.desc())  # Use created_at instead of timestamp
                    .limit(limit)
                    .all()
                )

                return [
                    MessageData(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.created_at  # Use created_at as timestamp
                    )
                    for msg in messages
                ]

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
            raise
