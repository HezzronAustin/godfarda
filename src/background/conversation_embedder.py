from typing import List, Dict, Any
import asyncio
import logging
from datetime import datetime
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from src.storage.database import session_scope, Message, Conversation, Agent
from src.agents.models import AgentExecution
from src.agents.factory import DynamicAgent
from langchain_community.chat_models.ollama import ChatOllama
import os

logger = logging.getLogger('background.conversation_embedder')

class ConversationEmbedder:
    def __init__(self, engine: Engine, embedding_model: str = "all-MiniLM-L6-v2"):
        self.engine = engine
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)
        self.vector_store = Chroma(
            collection_name="conversation_history",
            embedding_function=self.embeddings,
            persist_directory="./data/vectorstore"
        )
        
    async def process_agent_conversations(self, agent_id: int):
        """Process all unprocessed conversations for a specific agent"""
        logger.info(f"Processing conversations for agent {agent_id}")
        
        try:
            with session_scope(self.engine) as session:
                # Get agent and verify it exists
                agent_def = session.query(Agent).filter_by(id=agent_id).first()
                if not agent_def:
                    raise ValueError(f"Agent with id {agent_id} not found")
                
                # Initialize the DynamicAgent
                llm = ChatOllama(
                    model=agent_def.llm_model,
                    temperature=agent_def.temperature,
                    base_url=os.getenv('OLLAMA_BASE_URL')
                )
                dynamic_agent = DynamicAgent(agent_def, llm, session)
                
                # Get all executions for this agent that haven't been vectorized
                executions = (
                    session.query(AgentExecution)
                    .filter(
                        AgentExecution.agent_id == agent_id,
                        AgentExecution.status == 'completed',  # Only process completed executions
                        AgentExecution.is_vectorized == False  # Use explicit flag
                    )
                    .all()
                )
                
                if not executions:
                    logger.info(f"No unprocessed conversations found for agent {agent_id}")
                    return
                
                logger.info(f"Found {len(executions)} unprocessed conversations")
                
                for execution in executions:
                    # Get the conversation messages
                    conversation = execution.conversation
                    if not conversation:
                        continue
                        
                    messages = (
                        session.query(Message)
                        .filter(Message.conversation_id == conversation.id)
                        .order_by(Message.created_at)
                        .all()
                    )
                    
                    if not messages:
                        continue
                    
                    # Format conversation for the agent
                    conversation_text = "\n".join([
                        f"{msg.role}: {msg.content}"
                        for msg in messages
                    ])
                    
                    # Let the agent process the conversation
                    try:
                        agent_response = await dynamic_agent.process_message(
                            f"Process this conversation and create a memory context:\n\n{conversation_text}"
                        )
                        memory_context = agent_response.get('response', conversation_text)
                    except Exception as e:
                        logger.error(f"Error processing conversation with agent: {str(e)}")
                        memory_context = conversation_text
                    
                    # Create metadata
                    metadata = {
                        "agent_id": agent_id,
                        "conversation_id": conversation.id,
                        "execution_id": execution.id,
                        "user_id": conversation.user_id,
                        "timestamp": conversation.created_at.isoformat(),
                        "message_count": len(messages)
                    }
                    
                    # Add to vector store
                    self.vector_store.add_texts(
                        texts=[memory_context],
                        metadatas=[metadata]
                    )
                    
                    # Update execution record to mark as processed
                    execution.is_vectorized = True
                    execution.vectorized_at = datetime.utcnow()
                    execution.execution_data = {
                        **execution.execution_data if execution.execution_data else {},
                        "embedding_model": self.embeddings.model_name,
                        "memory_context_length": len(memory_context)
                    }
                    
                    logger.debug(f"Processed conversation {conversation.id} for execution {execution.id}")
                
                session.commit()
                logger.info(f"Successfully processed all conversations for agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Error processing conversations for agent {agent_id}: {str(e)}", exc_info=True)
            raise

    async def run_periodic(self, agent_id: int, interval_seconds: int = 300):
        """Run the conversation processing periodically"""
        while True:
            try:
                await self.process_agent_conversations(agent_id)
            except Exception as e:
                logger.error(f"Error in periodic processing: {str(e)}", exc_info=True)
            
            await asyncio.sleep(interval_seconds)
