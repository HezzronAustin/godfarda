# RAG (Retrieval-Augmented Generation) System

This directory contains the core RAG system implementation for the Godfarda AI system.

## Components

### core.py
The main RAG system implementation featuring:
- Document processing and embedding
- Context-aware retrieval
- Integration with ChromaDB
- Advanced conversation context building

## Key Features

- **Hybrid Search**: Combines semantic and keyword-based search
- **Dynamic Context Building**: Intelligent context construction for conversations
- **Vector Storage**: Efficient document embedding storage using ChromaDB
- **Conversation History**: Maintains and utilizes conversation context
- **Async Operations**: Full asynchronous support for all operations

## Usage

```python
from rag.core import RAGSystem

# Initialize the RAG system
rag_system = RAGSystem(
    chroma_client=chroma_client,
    embedding_model=embedding_model
)

# Query the system
results = await rag_system.query(
    query="your query",
    conversation_history=history
)
```

## Integration Points

- **Storage**: Interfaces with both ChromaDB and PostgreSQL
- **Agents**: Provides knowledge retrieval capabilities to agents
- **Tools**: Supports tool-augmented responses
