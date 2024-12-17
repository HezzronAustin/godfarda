# AI Models

The AI Tools Ecosystem provides a modular interface for working with different AI models. This system allows easy integration and switching between various AI providers.

## Architecture

The AI model system consists of these main components:

1. **AIModel Interface**: Abstract base class defining the common interface for all AI models
2. **Model Implementations**: Concrete implementations for specific AI providers
3. **AIModelFactory**: Factory class for creating and managing AI model instances
4. **Message & Response Types**: Standardized data structures for communication

## Available Models

### Ollama

Built-in support for Ollama models (llama2, codellama, etc.)

#### Configuration
```python
model = AIModelFactory.create(
    "ollama",
    model_name="llama2",  # or other available models
    base_url="http://localhost:11434/api"  # optional
)
```

## Using AI Models

### Basic Usage
```python
from src.tools.ai import AIModel, AIModelFactory, Message, MessageRole

# Create model instance
model = AIModelFactory.create("ollama", model_name="llama2")
await model.initialize()

# Send chat messages
response = await model.chat([
    Message(role=MessageRole.SYSTEM, content="You are a helpful assistant"),
    Message(role=MessageRole.USER, content="Hello!")
])

print(response.content)

# Clean up
await model.cleanup()
```

### Message Types
- **SYSTEM**: System instructions/context
- **USER**: User messages
- **ASSISTANT**: AI responses
- **FUNCTION**: Function calls/responses

## Adding New AI Models

1. Create a new class implementing the AIModel interface:
```python
from src.tools.ai import AIModel, Message, ModelResponse

class CustomAIModel(AIModel):
    async def initialize(self) -> bool:
        # Setup code
        pass
        
    async def chat(self,
                  messages: List[Message],
                  temperature: float = 0.7,
                  max_tokens: Optional[int] = None,
                  **kwargs) -> ModelResponse:
        # Chat implementation
        pass
        
    async def cleanup(self) -> None:
        # Cleanup code
        pass
```

2. Register with AIModelFactory:
```python
AIModelFactory.register("custom_model", CustomAIModel)
```

## Best Practices

1. **Error Handling**
   - Implement proper error handling in model implementations
   - Log errors and relevant context
   - Clean up resources in case of failures

2. **Resource Management**
   - Initialize resources in `initialize()`
   - Clean up properly in `cleanup()`
   - Use async context managers when appropriate

3. **Configuration**
   - Use environment variables for sensitive data
   - Make model parameters configurable
   - Document all configuration options

4. **Testing**
   - Write unit tests for model implementations
   - Include integration tests
   - Test error cases and edge conditions

## Configuration

AI models can be configured through environment variables or direct parameters:

```env
OLLAMA_BASE_URL=http://localhost:11434/api
OLLAMA_DEFAULT_MODEL=llama2
```

Or through code:
```python
model = AIModelFactory.create(
    "ollama",
    model_name="llama2",
    base_url="custom_url",
    temperature=0.8
)
```

## Error Handling

Models should handle common errors gracefully:

```python
try:
    response = await model.chat(messages)
except ConnectionError:
    logger.error("Failed to connect to AI service")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
finally:
    await model.cleanup()
```

## Testing

Refer to [TESTING.md](TESTING.md) for information about testing AI models.
