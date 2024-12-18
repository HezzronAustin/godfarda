# Data-Driven Agent System

A flexible, data-driven agent system that allows dynamic creation and chaining of AI agents with tools and functions.

## Architecture Overview

The system is built on three core components:

1. **Database Models** (`models.py`)
   - `Agent`: Stores agent definitions, prompts, and configurations
   - `Tool`: Defines external tools and their implementations
   - `Function`: Stores custom functions as Python code
   - `AgentExecution`: Tracks execution history and agent chaining

2. **Dynamic Agent Factory** (`factory.py`)
   - Creates agents from database definitions
   - Manages tool and function loading
   - Handles agent chaining and fallback logic
   - Tracks execution state and history

3. **Agent Registry** (`registry.py`)
   - Manages agent registration and lifecycle
   - Handles tool and function registration
   - Provides caching for active agents
   - Routes messages to appropriate agents

## Key Features

### Data-Driven Design
- Agents are defined in the database, not code
- Easy to create, modify, and version agents
- Dynamic loading of tools and functions
- Schema validation for inputs and outputs

### Controlled Agent Chaining
- `max_chain_depth` parameter prevents infinite recursion
- Fallback agent system for handling edge cases
- Execution tracking for monitoring chain depth
- Chain strategy configuration (sequential/parallel)

### Schema Validation
- Input/output validation using JSON schemas
- Ensures data consistency across agent chains
- Prevents invalid data propagation
- Helps maintain system reliability

### Execution Tracking
- Complete history of agent executions
- Parent-child relationship tracking
- Performance metrics and timing
- Error tracking and debugging support

## Usage Examples

### 1. Registering a Tool

```python
registry.register_tool(
    name="search_docs",
    description="Search documentation",
    function_name="src.tools.search.search_docs",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"}
        }
    },
    output_schema={
        "type": "array",
        "items": {"type": "string"}
    }
)
```

### 2. Creating an Agent

```python
registry.register_agent(
    name="DocSearchAgent",
    description="Helps search documentation",
    system_prompt="You help users find information in documentation...",
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "answer": {"type": "string"}
        }
    },
    tools=["search_docs"],
    max_chain_depth=2
)
```

### 3. Using the Agent System

```python
response = await registry.process(
    "How do I use the search function?",
    conversation_id="123"
)
```

## Best Practices

### Agent Design
1. **Clear Responsibility**
   - Each agent should have a single, well-defined purpose
   - Use clear input/output schemas
   - Include comprehensive descriptions

2. **Chain Control**
   - Set appropriate `max_chain_depth` for each agent
   - Use `fallback_agent_id` judiciously
   - Monitor chain execution metrics

3. **Schema Design**
   - Define strict input/output schemas
   - Include all required fields
   - Document schema expectations

### Performance Optimization
1. **Caching**
   - Use the registry's caching mechanism
   - Clear cache when appropriate
   - Monitor cache hit rates

2. **Chain Optimization**
   - Minimize chain depth where possible
   - Use parallel execution when appropriate
   - Monitor execution times

## Potential Improvements

### 1. Enhanced Chain Control
- Implement chain strategies (e.g., parallel, waterfall)
- Add chain abort conditions
- Support conditional chaining logic
- Add chain visualization tools

### 2. Advanced Monitoring
- Real-time execution monitoring
- Performance dashboards
- Chain optimization suggestions
- Anomaly detection

### 3. Schema Evolution
- Version control for schemas
- Schema migration tools
- Backward compatibility checks
- Schema validation caching

### 4. Dynamic Loading
- Hot-reload capability for agents
- Dynamic tool/function updates
- A/B testing support
- Canary deployments

### 5. Security Enhancements
- Role-based access control
- Agent isolation
- Rate limiting
- Audit logging

### 6. Testing Framework
- Agent simulation tools
- Chain testing utilities
- Performance benchmarking
- Regression testing

## Leveraging the Architecture

### 1. Custom Agent Types
Create specialized agents for different tasks:
- Data processing agents
- API integration agents
- Workflow automation agents
- Analysis and reporting agents

### 2. Agent Composition
Build complex workflows through agent composition:
- Sequential processing chains
- Parallel processing groups
- Conditional execution paths
- Error handling chains

### 3. Dynamic Updates
Leverage the data-driven nature for:
- A/B testing different prompts
- Gradual rollout of changes
- Quick fixes and updates
- Performance optimization

### 4. Integration Points
Extend the system through:
- Custom tool implementations
- External API integrations
- Database connectors
- Service integrations

## Contributing

When adding new features:
1. Follow the existing schema patterns
2. Add appropriate tests
3. Update documentation
4. Consider backward compatibility
5. Add migration scripts if needed

## Future Roadmap

1. **Enhanced Monitoring**
   - Real-time dashboards
   - Performance analytics
   - Chain visualization
   - Anomaly detection

2. **Advanced Chain Control**
   - Complex chain strategies
   - Dynamic chain optimization
   - Chain templates
   - Visual chain builder

3. **Integration Expansion**
   - More tool types
   - External service connectors
   - API integration templates
   - Custom function builders
