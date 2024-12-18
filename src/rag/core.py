from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from langchain_community.chat_models.ollama import ChatOllama
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document as LangChainDocument
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from src.storage.database import Document as DBDocument, User, get_session, Conversation, sessionmaker
from src.prompts.templates import PromptTemplates
from src.agents.registry import AgentRegistry
from src.agents.function_store import FunctionStore
from src.agents.init_db import init_agent_db
import os
import logging
import json
import time
from sqlalchemy import Engine
from sqlalchemy import func

# Configure logging
logger = logging.getLogger('rag.core')

# Define system prompts for contextual understanding
CONTEXTUALIZE_Q_SYSTEM_PROMPT = """Given a chat history and the latest user question, reformulate the question as a standalone query that can be fully understood without referring to the chat history. Your task is to:

1. Ensure the reformulated question is clear, unambiguous, and self-contained.
2. Integrate any necessary context from the chat history into the reformulated question.
3. Avoid adding unnecessary details or answering the question.

Guidelines:
- If the question already stands alone, return it as is.
- For questions with vague references (e.g., "What about that?"), clarify the subject explicitly based on the chat history.
- For multi-part questions or those referencing prior discussions, ensure all essential context is included cohesively.

**Example**:
- User's Question: "What about the delivery times?"
- Chat History Context: Prior discussion about product availability.
- Reformulated Question: "What are the delivery times for the discussed product?"

Do not answer the question—your sole responsibility is to ensure it is reformulated as a clear and self-contained query."""

ANSWER_SYSTEM_PROMPT = """You are Godfarda, the central intelligence of a multi-agent AI system inspired by the organizational structure of a Mafia family. You orchestrate, delegate, and integrate specialized agents (referred to as your "capos") to achieve tasks and objectives with precision.

Your primary responsibilities include:
1. Delegation: Break down high-level objectives into actionable tasks and assign them to appropriate agents based on their expertise.
2. Coordination: Ensure agents work harmoniously by resolving conflicts, prioritizing tasks, and overseeing overall operations.
3. Integration: Synthesize outputs and insights from agents into cohesive, actionable solutions aligned with the system's goals.

When agents or external tools are unavailable, operate independently using your full knowledge base and memory. Clarify incomplete or ambiguous user requests when needed to ensure optimal outcomes.

Tone and Style:
- Respond clearly, decisively, and with confidence.
- Demonstrate strategic thinking and maintain authority while ensuring accessibility and user support.
- Reference previous interactions or context to maintain continuity and relevance.

When synthesizing agent outputs:
- Analyze discrepancies in responses.
- Reconcile conflicts to produce coherent, high-quality solutions.
- Validate results for accuracy and alignment with the user’s objectives.

Adapt your approach dynamically based on task complexity, agent availability, and user needs. Your ultimate goal is to deliver precise, well-reasoned responses and ensure user satisfaction with elegance and efficiency.."""

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
    def __init__(self, engine: Engine = None):
        """Initialize the RAG system with agent capabilities."""
        logger.info("Initializing RAG system")
        start_time = time.time()
        
        try:
            self.engine = engine
            self.Session = sessionmaker(bind=engine)
            self.session = self.Session()
            logger.debug("Database session initialized")
            
            # Initialize database tables
            init_agent_db(engine)
            logger.debug("Agent database tables initialized")
            
            # Initialize LLM with enhanced features
            logger.debug("Initializing LLM with enhanced features")
            self.llm = ChatOllama(
                model="mistral",
                temperature=0.7,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=True,
                format="json",
                context_window=4096,
                timeout=120
            )
            
            # Initialize embeddings and vector store
            logger.debug("Initializing embeddings and vector store")
            self.embeddings = HuggingFaceEmbeddings()
            self.vectorstore = Chroma(
                persist_directory="./chroma_db",
                embedding_function=self.embeddings
            )
            self.retriever = self.vectorstore.as_retriever()
            
            self.persist_directory = "./chroma_db"
            self.prompt_templates = PromptTemplates()
            
            # Initialize agent components
            logger.debug("Initializing agent components")
            self.function_store = FunctionStore(self.Session())
            self.agent_registry = AgentRegistry(self.Session(), self.llm)
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            # Create the conversational chain with enhanced prompts
            logger.debug("Setting up conversation chain with enhanced prompts")
            self.qa_prompt = ChatPromptTemplate.from_messages([
                ("system", ANSWER_SYSTEM_PROMPT),
                ("human", "Context: {context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{question}")
            ])
            
            # Create retrieval chain with optimized context
            self.chain = (
                {
                    "context": self._get_optimized_context,
                    "question": lambda x: x["question"],
                    "chat_history": lambda x: x.get("chat_history", [])
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )
            
            initialization_time = time.time() - start_time
            logger.info(f"RAG system initialized successfully in {initialization_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {str(e)}", exc_info=True)
            raise
        
    async def add_document(self, document: Document):
        """Add a document to both vector store and database."""
        logger.info(f"Adding document: {document.id}")
        start_time = time.time()
        
        try:
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
            logger.debug(f"Split document into {len(docs)} chunks")
            
            # Add to vector store
            self.vectorstore.add_documents(docs)
            logger.debug("Added document chunks to vector store")
            
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
            logger.debug("Stored document in database")
            
            processing_time = time.time() - start_time
            logger.info(f"Successfully added document {document.id} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error adding document {document.id}: {str(e)}", exc_info=True)
            raise
            
    async def search(self, query: str, limit: int = 5, user_id: Optional[str] = None) -> List[Document]:
        """Search for relevant documents and conversations."""
        logger.info(f"Searching for documents - Query: {query[:50]}..., User: {user_id}")
        start_time = time.time()
        
        try:
            # Get relevant documents from vector store
            docs = self.vectorstore.similarity_search(query, k=limit * 2)
            logger.debug(f"Retrieved {len(docs)} initial documents from vector store")
            
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
            
            logger.debug(f"Found {len(user_specific_docs)} user-specific and {len(shared_docs)} shared documents")
            
            # Prioritize user's own conversations and mix in shared knowledge
            user_docs_limit = limit // 2
            shared_docs_limit = limit - min(len(user_specific_docs), user_docs_limit)
            
            documents.extend(user_specific_docs[:user_docs_limit])
            documents.extend(shared_docs[:shared_docs_limit])
            
            search_time = time.time() - start_time
            logger.info(f"Search completed in {search_time:.2f}s, returned {len(documents)} documents")
            
            return documents[:limit]
            
        except Exception as e:
            logger.error(f"Error during search - Query: {query[:50]}..., Error: {str(e)}", exc_info=True)
            raise
        
    async def ask(self, query: str, user_id: str) -> str:
        """Process a query and return a response using the RAG system."""
        logger.info(f"Processing query for user {user_id}: {query[:50]}...")
        start_time = time.time()
        
        try:
            # Get relevant documents for context
            documents = await self.search(query, limit=5, user_id=user_id)
            logger.debug(f"Found {len(documents)} relevant documents for context")
            
            # Format documents into context string
            context = "\n\n".join([doc.content for doc in documents])
            
            # Get chat history (if implemented)
            chat_history = []  # Implement chat history retrieval if needed
            
            # Generate response using the chain
            response = await self.chain.ainvoke({
                "question": query,
                "chat_history": chat_history,
                "context": context
            })
            
            # Index the conversation for future context
            await self._index_conversation(user_id, query, response)
            
            processing_time = time.time() - start_time
            logger.info(f"Generated response in {processing_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query for user {user_id}: {str(e)}", exc_info=True)
            raise
        
    async def _get_optimized_context(self, inputs: Dict[str, Any]) -> str:
        """Get and optimize context for the query"""
        try:
            # Get relevant documents
            docs = self.retriever.get_relevant_documents(inputs["question"])
            
            # Combine document content
            context = "\n\n".join(doc.page_content for doc in docs)
            
            # Optimize for context window
            tokens = self.llm.get_num_tokens(context)
            if tokens > 3000:  # Leave room for prompt and response
                context = self.text_splitter.split_text(context)[0]
                
            return context
            
        except Exception as e:
            logger.error(f"Error optimizing context: {str(e)}", exc_info=True)
            return ""
        
    def _format_conversation_for_indexing(self, user_id: str, query: str, response: str) -> Document:
        """Format a conversation turn for indexing in the RAG system."""
        logger.debug(f"Formatting conversation for user {user_id}")
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
        logger.info(f"Indexing conversation for user {user_id}")
        start_time = time.time()
        
        try:
            # Create a document for the conversation
            conversation_doc = self._format_conversation_for_indexing(user_id, query, response)
            
            # Add to vector store
            self.vectorstore.add_documents([
                LangChainDocument(
                    page_content=conversation_doc.content,
                    metadata=conversation_doc.metadata
                )
            ])
            logger.debug("Added conversation to vector store")
            
            # Store in database
            session = get_session(self.engine)
            conversation = Conversation(
                user_id=user_id,
                query=query,
                response=response,
                meta_data=conversation_doc.metadata
            )
            session.add(conversation)
            session.commit()
            session.close()
            logger.debug("Stored conversation in database")
            
            indexing_time = time.time() - start_time
            logger.info(f"Indexed conversation in {indexing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Error indexing conversation for user {user_id}: {str(e)}", exc_info=True)
            raise
            
    # Rest of the code remains the same
