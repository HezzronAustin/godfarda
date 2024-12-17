# Agent Interaction Guide

This document describes how to interact with agents in the AI Tools Ecosystem, including message formats, expected inputs/outputs, and best practices.

## Message Format

All agents expect messages in the following format:

```json
{
    "message": "The actual message content",
    "user_info": {
        "id": "unique_user_id",
        "name": "User's Display Name",
        "username": "username",
        "first_name": "First",
        "last_name": "Last"
    },
    "platform": "platform_identifier"
}
```

### Response Format

Agents respond with a standardized format:

```json
{
    "response": "The agent's response message",
    "agent": "agent_name",
    "error": "Error message if something went wrong (optional)"
}
```

## Available Agents

### GodFarda Agent

The top-level orchestrator agent that manages all other agents.

- **Direct Interaction**: Send general queries or requests
- **Agent Delegation**: Use `@agent_name message` syntax to delegate to specific agents
- **Capabilities**: 
  - Understands and routes requests to appropriate agents
  - Maintains conversation context
  - Coordinates between multiple agents

### Text Agent

Specialized in text-based operations.

- **Capabilities**:
  - Conversational dialogue
  - Information queries
  - Text generation
  - Summarization
  - Language translation
  - Sentiment analysis

### Communications Agent

Handles communication across different platforms.

- **Capabilities**:
  - Message routing
  - Platform-specific formatting
  - Communication protocol handling

## Command Line Interface

The `agent_cli.py` provides a command-line interface for interacting with agents:

### List Available Agents
```bash
python3 src/agents/agent_cli.py list
```

### Interact with an Agent
```bash
python3 src/agents/agent_cli.py interact --agent godfarda --message "Your message"
```

### Delegate to Specific Agent
```bash
python3 src/agents/agent_cli.py interact --agent godfarda --message "@agentname Your message"
```

## Best Practices

1. **Message Structure**
   - Always provide complete user information
   - Include platform identifier
   - Use clear, specific messages

2. **Agent Selection**
   - Use GodFarda for general queries
   - Use `@agent_name` for specific capabilities
   - Let GodFarda suggest appropriate agents when unsure

3. **Error Handling**
   - Check for error field in responses
   - Retry with clarified input if needed
   - Follow agent suggestions for better results

## Common Patterns

1. **Information Query**
```json
{
    "message": "What's the weather like?",
    "user_info": {...},
    "platform": "cli"
}
```

2. **Agent Delegation**
```json
{
    "message": "@textagent Summarize this article...",
    "user_info": {...},
    "platform": "telegram"
}
```

3. **Error Response**
```json
{
    "error": "Failed to process message",
    "response": "Please try rephrasing your request"
}
```
