# Godfarda - Advanced AI System

An advanced AI system combining RAG (Retrieval-Augmented Generation), recursive minion agents, and dynamic tools.

## Features

- RAG System with ChromaDB and PostgreSQL
- Recursive Minion Agents with Dynamic Creation
- Advanced Tool Management System
- Type-safe Implementation with Pydantic
- Async Support
- Comprehensive Monitoring and Logging System
- Telegram Bot Integration

## Project Structure

```
godfarda/
├── src/
│   ├── rag/           # RAG system implementation
│   ├── agents/        # Agent system and tools
│   ├── tools/         # Tool definitions and implementations
│   ├── models/        # Data models and schemas
│   ├── storage/       # Database and storage implementations
│   └── utils/         # Utility functions and configurations
├── tests/            # Test suite
├── config/           # Configuration files
├── logs/            # Application logs directory
└── docs/            # Documentation
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

## Logging System

The application implements a comprehensive logging system with the following features:

### Log Files
- General logs: `logs/godfarda_YYYYMMDD.log`
- Error logs: `logs/godfarda_error_YYYYMMDD.log`
- Rotating file system (10MB per file, 5 backups)
- UTF-8 encoding

### Log Levels
- DEBUG: Detailed debugging information
- INFO: General operational messages
- WARNING: Warning messages for potential issues
- ERROR: Error messages with full tracebacks

### Components Logged
- Telegram Bot operations
- RAG system operations
- Agent system activities
- Database operations
- System initialization and shutdown

### Monitoring
All logs include:
- Timestamp
- Component name
- Log level
- Detailed message
- Exception tracebacks (for errors)
- Performance metrics

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

## Telegram Bot Usage

The system includes a Telegram bot interface. To use it:

1. Set up Telegram credentials in `.env`:
```
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
```

2. Run the bot:
```bash
python telegram_bot.py
```

Available commands:
- `/ask [question]`: Ask a question to the system
- Direct messages are also treated as questions

## License

MIT License
