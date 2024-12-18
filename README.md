# Godfarda - Advanced AI System

An advanced AI system combining RAG (Retrieval-Augmented Generation), recursive minion agents, and dynamic tools.

## Features

- RAG System with ChromaDB and PostgreSQL
- Recursive Minion Agents with Dynamic Creation
- Advanced Tool Management System
- Type-safe Implementation with Pydantic
- Async Support
- Comprehensive Monitoring

## Project Structure

```
godfarda/
├── src/
│   ├── rag/
│   ├── agents/
│   ├── tools/
│   ├── models/
│   ├── storage/
│   └── utils/
├── tests/
├── config/
└── docs/
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Initialize the database:
```bash
python scripts/init_db.py
```

## Database Setup

The application uses SQLite for data storage. The database schema includes the following tables:
- `documents`: Stores document content and embeddings
- `conversations`: Maintains conversation history
- `agent_states`: Tracks agent state information

To initialize the database:
```bash
python init_db.py
```

This will create all necessary tables and set up the database structure. The database file `godfarda.db` will be created in the root directory.

## Usage

Basic example of using the system:

```python
from godfarda.rag import RAGSystem
from godfarda.agents import ChainableMinion
from godfarda.tools import ToolManager

# Initialize system
rag_system = RAGSystem()
root_agent = ChainableMinion(name="root")

# Process query
result = await root_agent.process_query("Your query here")
```

## License

MIT License
