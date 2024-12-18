# Agent System

A flexible, data-driven agent system that enables dynamic creation and chaining of AI agents with tools and functions.

## Core Components

1. **Base Agent** (`base.py`)
   - Abstract base class for all agents
   - Message processing interface
   - Chat history formatting
   - Response standardization

2. **Dynamic Agent Factory** (`factory.py`)
   - Creates agents from database definitions
   - Comprehensive logging and monitoring
   - Tool and function loading
   - Execution tracking with performance metrics
   - Error handling with detailed logging

3. **Function Store** (`function_store.py`)
   - Secure function storage and execution
   - Code validation and sandboxing
   - Version control and hashing
   - Memory and timeout limits
   - Allowed imports management

4. **Database Models** (`models.py`)
   - Agent definitions and configurations
   - Tool and function specifications
   - Execution history tracking
   - Agent relationships and chaining
   - JSON schema validation

5. **Agent Registry** (`registry.py`)
   - Agent lifecycle management
   - Message routing and handling
   - Caching for active agents
   - Performance monitoring
   - Error tracking and logging

6. **Minion System** (`minion.py`)
   - Task delegation and processing
   - Capability-based routing
   - Tool execution management
   - State tracking
   - Error handling

7. **Database Initialization** (`init_db.py`)
   - Schema creation and updates
   - Default agent setup
   - Configuration management
   - Migration handling

## Features

### Secure Function Execution
- Code validation and sandboxing
- Memory and timeout limits
- Restricted imports and builtins
- Version control and hashing
- Execution monitoring

### Comprehensive Logging
- Detailed operation logging
- Performance metrics tracking
- Error tracking with context
- Execution history
- State preservation

### Dynamic Agent Creation
- Database-driven definitions
- Runtime agent creation
- Tool and function loading
- Configuration management
- Schema validation

### Task Management
- Capability-based routing
- Task delegation
- State tracking
- Error handling
- Performance monitoring

### Database Integration
- SQLAlchemy models
- JSON schema validation
- Relationship management
- Execution tracking
- Configuration storage

## Usage Examples

### Creating an Agent

```python
from src.agents.registry import AgentRegistry
from src.agents.models import Agent

# Initialize registry
registry = AgentRegistry(session)

# Create agent definition
agent_def = Agent(
    name="SearchAgent",
    description="Handles search queries",
    system_prompt="You are a search assistant...",
    input_schema={"type": "object", "properties": {...}},
    output_schema={"type": "object", "properties": {...}},
    config_data={"capabilities": ["search", "filter"]},
    max_chain_depth=3
)

# Register agent
agent = registry.register_agent(agent_def)
```

### Processing Messages

```python
# Process messages with automatic routing
response = await registry.process(
    messages=[HumanMessage(content="Search for...")],
    conversation_id="123"
)

# Direct agent usage
agent = registry.get_agent("SearchAgent")
result = await agent.process_message("Search for...")
```

### Function Management

```python
from src.agents.function_store import FunctionStore

# Initialize store
store = FunctionStore(session)

# Store function
await store.store_function(
    name="search_docs",
    code="""async def search_docs(query: str) -> List[str]:
        # Implementation
        return results
    """,
    description="Search documentation",
    input_schema={"type": "object", "properties": {...}},
    output_schema={"type": "object", "properties": {...}},
    is_async=True
)

# Execute function
result = await store.execute_function("search_docs", {"query": "..."})
```

## Configuration

### Agent Configuration
```python
{
    "type": "agent",
    "capabilities": ["search", "filter"],
    "max_chain_depth": 3,
    "chain_strategy": "sequential",
    "temperature": 0.7,
    "top_p": 1.0,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0
}
```

### Function Configuration
```python
{
    "version": "1.0",
    "is_async": true,
    "requires_context": false,
    "memory_limit": 512,  # MB
    "timeout": 30,        # seconds
    "safe_mode": true,
    "allowed_imports": [
        "json", "datetime", "math", "re",
        "collections", "itertools", "functools"
    ]
}
```

## Best Practices

### Security
1. Always validate function code
2. Use memory and timeout limits
3. Restrict imports and builtins
4. Implement proper error handling
5. Log security-related events

### Performance
1. Use agent caching appropriately
2. Monitor execution times
3. Track resource usage
4. Optimize chain depth
5. Use appropriate timeouts

### Development
1. Follow type hints
2. Add comprehensive logging
3. Include error handling
4. Write unit tests
5. Document changes

### Monitoring
1. Track execution metrics
2. Monitor error patterns
3. Log performance data
4. Analyze chain operations
5. Review security events

## Error Handling

### Execution Errors
- Log full error context
- Track error patterns
- Implement fallbacks
- Preserve error state
- Notify monitoring

### Chain Errors
- Handle depth limits
- Manage timeouts
- Track chain state
- Log chain operations
- Implement recovery

## Future Improvements

1. **Enhanced Monitoring**
   - Real-time dashboards
   - Performance analytics
   - Chain visualization
   - Anomaly detection

2. **Security Enhancements**
   - Role-based access
   - Enhanced sandboxing
   - Audit logging
   - Threat detection

3. **Performance Optimization**
   - Caching improvements
   - Chain optimization
   - Resource management
   - Query optimization

4. **Development Tools**
   - Testing framework
   - Development console
   - Debugging tools
   - Documentation generator
