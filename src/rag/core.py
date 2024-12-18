from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from langchain.llms import Ollama
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.storage.database import Document as DBDocument, User, get_session, Conversation, sessionmaker
from src.prompts.templates import PromptTemplates
import os
import logging
import json
from sqlalchemy import Engine
from sqlalchemy import func

# Define system prompts for contextual understanding
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question 
which might reference context in the chat history, formulate a standalone question which 
can be understood without the chat history. Do NOT answer the question, just reformulate 
it if needed and otherwise return it as is."""

ANSWER_SYSTEM_PROMPT = """You are a helpful AI assistant with access to relevant information 
about the user and conversation history. Use the provided context and chat history to give 
accurate, helpful, and contextually relevant responses."""

@dataclass
class Message:
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

class Document(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class RAGSystem:
    def __init__(self, engine: Engine, persist_directory: str = "./chroma_db"):
        """Initialize the RAG system with conversational capabilities."""
        self.engine = engine
        
        # Initialize LLM
        self.llm = Ollama(model="mistral")
        
        # Initialize embeddings and vector store
        self.embeddings = HuggingFaceEmbeddings()
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )
        self.retriever = self.vectorstore.as_retriever()
        
        self.persist_directory = persist_directory
        self.prompt_templates = PromptTemplates()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # Create the conversational chain
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", ANSWER_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            ("human", "Context: {context}")
        ])
        
        # Create retrieval chain
        self.chain = (
            {
                "context": lambda x: self.retriever.get_relevant_documents(x["question"]),
                "question": lambda x: x["question"],
                "chat_history": lambda x: x.get("chat_history", [])
            }
            | self.qa_prompt
            | self.llm
            | StrOutputParser()
        )
        
        logging.info("RAG system initialized successfully")
        
    async def add_document(self, document: Document):
        # Convert to LangChain document format
        langchain_doc = LangChainDocument(
            page_content=document.content,
            metadata={
                "id": document.id,
                **document.metadata
            }
        )
        
        # Split text if needed
        docs = self.text_splitter.split_documents([langchain_doc])
        
        # Add to vector store
        self.vectorstore.add_documents(docs)
        
        # Store in SQLite
        session = get_session(self.engine)
        db_doc = DBDocument(
            external_id=document.id,
            content=document.content,
            meta_data=document.metadata,
            embedding_id=document.id
        )
        session.add(db_doc)
        session.commit()
        session.close()
            
    async def search(self, query: str, limit: int = 5, user_id: Optional[str] = None) -> List[Document]:
        """Search for relevant documents and conversations."""
        # Get relevant documents from vector store
        docs = self.vectorstore.similarity_search(query, k=limit * 2)  # Get more docs initially for filtering
        
        # Convert to our Document format
        documents = []
        user_specific_docs = []
        shared_docs = []
        
        for doc in docs:
            document = Document(
                id=doc.metadata.get('external_id', 'unknown'),
                content=doc.page_content,
                metadata=doc.metadata
            )
            
            # Separate user-specific conversations from shared knowledge
            if doc.metadata.get('type') == 'conversation':
                if doc.metadata.get('user_id') == user_id:
                    user_specific_docs.append(document)
                else:
                    shared_docs.append(document)
            else:
                shared_docs.append(document)
        
        # Prioritize user's own conversations and mix in shared knowledge
        # Try to maintain a balance: if limit is 5, get ~2 user-specific and ~3 shared
        user_docs_limit = limit // 2
        shared_docs_limit = limit - min(len(user_specific_docs), user_docs_limit)
        
        documents.extend(user_specific_docs[:user_docs_limit])
        documents.extend(shared_docs[:shared_docs_limit])
        
        return documents[:limit]
        
    def _format_conversation_for_indexing(self, user_id: str, query: str, response: str) -> Document:
        """Format a conversation turn for indexing in the RAG system."""
        conversation_id = f"conversation_{user_id}_{datetime.utcnow().timestamp()}"
        return Document(
            id=conversation_id,
            content=f"User: {query}\nAssistant: {response}",
            metadata={
                "type": "conversation",
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "query": query,
                "response": response,
                "is_shared": True  # Mark all conversations as shared knowledge
            }
        )
        
    async def _index_conversation(self, user_id: str, query: str, response: str):
        """Index the conversation in both vector store and database."""
        # Create a document for the conversation
        conversation_doc = self._format_conversation_for_indexing(user_id, query, response)
        
        # Add to vector store
        self.vectorstore.add_documents([
            LangChainDocument(
                page_content=conversation_doc.content,
                metadata=conversation_doc.metadata
            )
        ])
        
        # Store in database
        with get_session(self.engine) as session:
            db_doc = DBDocument(
                external_id=conversation_doc.id,
                content=conversation_doc.content,
                meta_data=conversation_doc.metadata,
                embedding_id=None  # The vector store handles embeddings
            )
            session.add(db_doc)
            session.commit()
            
    def get_context(self, query: str, user_id: str, max_results: int = 5) -> List[Document]:
        """
        Get context for a query, combining both user-specific and shared knowledge.
        
        Args:
            query: The user's query
            user_id: Telegram user ID
            max_results: Maximum number of documents to return
        """
        # Split results between personal and shared context
        personal_limit = max_results // 2
        shared_limit = max_results - personal_limit
        
        # Get user-specific context
        personal_context = self.vectorstore.similarity_search(
            query,
            k=personal_limit,
            filter={"user_id": user_id}
        )
        
        # Get shared context from other users' conversations
        shared_context = self.vectorstore.similarity_search(
            query,
            k=shared_limit,
            filter={"type": "conversation"}  # Simplified filter to just get conversations
        )
        
        # Combine and sort by relevance
        all_context = []
        for doc in personal_context:
            doc.metadata["context_type"] = "personal"
            all_context.append(doc)
        for doc in shared_context:
            doc.metadata["context_type"] = "shared"
            all_context.append(doc)
            
        return all_context

    def _format_context(self, documents: List[Document]) -> str:
        """Format context with clear source indicators."""
        if not documents:
            return "No relevant context found."
        
        formatted_contexts = []
        for doc in documents:
            doc_type = doc.metadata.get('type', 'document')
            formatted_context = self.prompt_templates.format_context(
                document_type=doc_type,
                content=doc.content
            )
            formatted_contexts.append(formatted_context)
            
        return "\n\n".join(formatted_contexts)

    def _get_recent_interactions(self, telegram_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent interactions for a user from the database.
        
        Args:
            telegram_id: Telegram user ID
            limit: Maximum number of recent interactions to retrieve
        
        Returns:
            List of recent interactions with their metadata
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        try:
            # First get the user by telegram_id
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            
            if not user:
                logging.warning(f"No user found for telegram_id {telegram_id}")
                return []
            
            # Query recent conversations for this user using the user's database ID
            conversations = (
                session.query(Conversation)
                .filter(Conversation.user_id == user.id)  # Use the user's database ID
                .order_by(Conversation.timestamp.desc())
                .limit(limit)
                .all()
            )
            
            # Format conversations
            interactions = []
            for conv in conversations:
                interactions.append({
                    "query": conv.query,
                    "response": conv.response,
                    "timestamp": conv.timestamp,
                    "meta_data": conv.meta_data
                })
            
            if not interactions:
                logging.info(f"No interactions found for user {telegram_id}")
            else:
                logging.info(f"Found {len(interactions)} interactions for user {telegram_id}")
            
            return interactions
            
        except Exception as e:
            logging.error(f"Error retrieving conversations: {e}")
            return []
            
        finally:
            session.close()

    def _format_conversation_history(self, interactions: List[Dict[str, Any]]) -> str:
        """Format conversation history into a readable string."""
        if not interactions:
            return "No previous conversation history."
            
        history = []
        # Reverse to show oldest first
        for interaction in reversed(interactions):
            history.extend([
                f"User: {interaction['query']}",
                f"Assistant: {interaction['response']}"
            ])
        
        return "\n".join(history)

    def _build_conversation_context(self, user: User, query: str) -> Dict[str, Any]:
        """
        Build a comprehensive conversation context including user information,
        conversation patterns, and relevant details from past interactions.
        """
        # Get recent interactions using telegram_id
        recent_interactions = self._get_recent_interactions(user.telegram_id)
        
        # Build conversation history
        conversation_history = self._format_conversation_history(recent_interactions)
        
        # Get basic user context
        context = {
            "user": {
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or "User",
                "username": user.username,
                "telegram_id": user.telegram_id,
                "interaction_history": {
                    "first_interaction": user.created_at.strftime('%Y-%m-%d'),
                    "last_active": user.last_active.strftime('%Y-%m-%d %H:%M:%S'),
                    "total_interactions": len(recent_interactions)
                }
            },
            "conversation": {
                "history": conversation_history,
                "current_topic": self._identify_topic(query, recent_interactions),
                "recent_topics": self._extract_recent_topics(recent_interactions),
                "interaction_patterns": self._analyze_interaction_patterns(recent_interactions)
            },
            "preferences": user.preferences or {}
        }
        
        return context, recent_interactions

    async def ask(self, query: str, user_id: str, user_info: Dict[str, str] = None) -> str:
        """
        Process a query with enhanced context awareness.
        
        Args:
            query: User's question
            user_id: Telegram user ID
            user_info: Optional dictionary with user information
        """
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        try:
            # Get or create user record
            user = self.get_or_create_user(
                telegram_id=user_id,
                username=user_info.get('username') if user_info else None,
                first_name=user_info.get('first_name') if user_info else None,
                last_name=user_info.get('last_name') if user_info else None
            )
            user = session.merge(user)
            
            # Get recent interactions and format them as messages
            recent_interactions = self._get_recent_interactions(user_id)
            chat_history = []
            for interaction in reversed(recent_interactions):
                chat_history.extend([
                    HumanMessage(content=interaction['query']),
                    AIMessage(content=interaction['response'])
                ])
            
            # Use the RAG chain with chat history
            response = await self.chain.ainvoke({
                "question": query,
                "chat_history": chat_history
            })
            
            # Store the interaction
            timestamp = datetime.utcnow().isoformat()
            data = {
                "user_id": user.id,
                "query": query,
                "response": response,
                "timestamp": timestamp,
                "platform": "telegram",
                "conversation_meta": {
                    "telegram_id": user.telegram_id,
                    "platform": "telegram",
                    "speaker_type": "ai_assistant",
                    "interaction_type": "direct_message",
                    "context_used": True,
                    "history_used": bool(chat_history),
                    "user_info": {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "name": f"{user.first_name or ''} {user.last_name or ''}".strip()
                    }
                }
            }
            self._store_interaction_data(data)
            
            return response
            
        finally:
            session.close()

    def _store_interaction_data(self, data: Dict[str, Any]):
        """Store interaction data in the database."""
        # Create a new session
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        try:
            # Convert timestamp string to datetime object
            timestamp = datetime.fromisoformat(data["timestamp"]) if isinstance(data["timestamp"], str) else data["timestamp"]
            
            # Prepare metadata
            meta_data = {
                "platform": data["platform"],
                **data.get("conversation_meta", {})
            }
            
            # Create a new interaction record
            interaction = Conversation(
                user_id=data["user_id"],  # This links the conversation to the user
                query=data["query"],
                response=data["response"],
                timestamp=timestamp,
                meta_data=meta_data,
                context={}  # Empty context as it's not provided in the data
            )
            
            # Add and commit the interaction
            session.add(interaction)
            session.commit()
            
            logging.info(f"Stored interaction for user {data['user_id']}")
            
        except Exception as e:
            logging.error(f"Error storing interaction in database: {e}")
            session.rollback()
            raise
        
        finally:
            session.close()

    def _get_conversation_context(self, user_id: str, limit: int = 5) -> str:
        """Get the recent conversation history for a user."""
        # Get recent interactions from database
        interactions = self._get_recent_interactions(user_id, limit)
        return self._format_conversation_history(interactions)

    def _identify_topic(self, query: str, recent_interactions: List[Dict[str, Any]]) -> str:
        """Identify the current conversation topic based on query and recent history."""
        if not recent_interactions:
            return "New conversation"
            
        # Get the most recent interaction
        last_interaction = recent_interactions[0]
        
        # Simple topic continuity check
        if self._is_follow_up(query, last_interaction['query']):
            return "Follow-up to previous conversation"
        
        return "New topic"

    def _is_follow_up(self, current_query: str, previous_query: str) -> bool:
        """Check if the current query is a follow-up to the previous one."""
        follow_up_indicators = [
            "what about",
            "and then",
            "so what",
            "why",
            "how about",
            "what else",
            "tell me more",
            "can you explain",
            "what if",
            "is there"
        ]
        
        current_lower = current_query.lower()
        return any(indicator in current_lower for indicator in follow_up_indicators)

    def _extract_recent_topics(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Extract main topics from recent conversations."""
        topics = []
        for interaction in interactions[:3]:  # Look at last 3 interactions
            query = interaction['query']
            # Simple topic extraction - first few words
            topic = " ".join(query.split()[:5]) + "..."
            topics.append(topic)
        return topics

    def _analyze_interaction_patterns(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in user interactions."""
        if not interactions:
            return {
                "pattern": "First interaction",
                "interaction_frequency": "First interaction",
                "common_topics": [],
                "conversation_style": "Not enough data"
            }
            
        try:
            return {
                "pattern": "Regular user" if len(interactions) > 5 else "New user",
                "interaction_frequency": self._calculate_interaction_frequency(interactions),
                "common_topics": self._identify_common_topics(interactions),
                "conversation_style": self._identify_conversation_style(interactions)
            }
        except Exception as e:
            logging.error(f"Error analyzing interaction patterns: {e}")
            return {
                "pattern": "Error analyzing patterns",
                "interaction_frequency": "Unknown",
                "common_topics": [],
                "conversation_style": "Unknown"
            }

    def _calculate_interaction_frequency(self, interactions: List[Dict[str, Any]]) -> str:
        """Calculate how frequently the user interacts with the system."""
        if not interactions:
            return "First interaction"
            
        try:
            first_interaction = interactions[-1]['timestamp']
            last_interaction = interactions[0]['timestamp']
            
            # Calculate time difference
            time_diff = last_interaction - first_interaction
            total_interactions = len(interactions)
            
            # Calculate frequency
            if time_diff.days == 0:
                return "Multiple interactions today"
            elif time_diff.days < 7:
                avg_per_day = total_interactions / (time_diff.days + 1)
                return f"Average {avg_per_day:.1f} interactions per day"
            else:
                avg_per_week = total_interactions / ((time_diff.days / 7) + 1)
                return f"Average {avg_per_week:.1f} interactions per week"
                
        except Exception as e:
            logging.error(f"Error calculating interaction frequency: {e}")
            return "Unable to calculate interaction frequency"

    def _identify_common_topics(self, interactions: List[Dict[str, Any]]) -> List[str]:
        """Identify common topics in user's interactions."""
        # Simple implementation - just return last few unique queries
        unique_queries = set()
        topics = []
        for interaction in interactions:
            query = interaction['query']
            if query not in unique_queries and len(topics) < 3:
                unique_queries.add(query)
                topics.append(query)
        return topics

    def _identify_conversation_style(self, interactions: List[Dict[str, Any]]) -> str:
        """Identify user's conversation style."""
        queries = [interaction['query'] for interaction in interactions]
        avg_length = sum(len(q.split()) for q in queries) / len(queries)
        
        if avg_length < 5:
            return "Concise"
        elif avg_length < 15:
            return "Balanced"
        else:
            return "Detailed"

    def get_or_create_user(self, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None) -> User:
        """Get or create a user record."""
        Session = sessionmaker(bind=self.engine)
        session = Session()
        
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            
            if not user:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
                session.commit()
                # Refresh the user object to ensure all attributes are loaded
                session.refresh(user)
            else:
                # Update last active
                user.last_active = datetime.utcnow()
                if username and username != user.username:
                    user.username = username
                if first_name and first_name != user.first_name:
                    user.first_name = first_name
                if last_name and last_name != user.last_name:
                    user.last_name = last_name
                session.commit()
                # Refresh the user object to ensure all attributes are loaded
                session.refresh(user)
            
            # Expunge the object from session but keep it in a detached state with loaded attributes
            session.expunge(user)
            return user
            
        finally:
            session.close()
