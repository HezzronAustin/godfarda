# Agents Directory

This directory contains the implementation of recursive minion agents in the Godfarda AI system.

## Components

### minion.py
The core implementation of recursive minion agents that can:
- Execute tasks autonomously
- Create and manage sub-agents
- Handle dynamic tool allocation
- Process and respond to complex queries

## Key Features

- **Recursive Agent Creation**: Ability to spawn and manage sub-agents for complex tasks
- **Dynamic Tool Management**: Flexible tool allocation based on task requirements
- **State Management**: Robust handling of agent states and contexts
- **Async Support**: Asynchronous execution of agent tasks

## Usage

```python
from agents.minion import MinionAgent

# Create a new minion agent
agent = MinionAgent(
    name="task_agent",
    tools=available_tools,
    context=task_context
)

# Execute a task
result = await agent.execute_task(task_description)
```

## Integration with RAG System

The agents are designed to work seamlessly with the RAG system, allowing them to:
- Access and query the knowledge base
- Use retrieved information for task execution
- Update the knowledge base with new information
