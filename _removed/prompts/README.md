# Prompts Directory

This directory contains the prompt templates and management system for the Godfarda AI system.

## Components

### templates.py
Contains structured prompt templates for:
- Agent instructions
- RAG system queries
- Tool usage
- Response formatting

## Key Features

- **Structured Templates**: Well-defined prompt structures for consistent outputs
- **Dynamic Formatting**: Template variables for context-specific prompts
- **Role-based Prompts**: Specialized prompts for different agent roles
- **Conversation Management**: Templates for maintaining conversation context

## Usage

```python
from prompts.templates import AgentPrompt, RAGPrompt

# Create an agent prompt
agent_prompt = AgentPrompt.format(
    task=task_description,
    context=context_data
)

# Create a RAG query prompt
rag_prompt = RAGPrompt.format(
    query=user_query,
    history=conversation_history
)
```

## Best Practices

- Keep prompts clear and concise
- Use consistent formatting across templates
- Include necessary context without overloading
- Maintain prompt versioning for different use cases
