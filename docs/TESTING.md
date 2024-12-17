# AI Tools Ecosystem Testing Guide

This document provides instructions for running various tests in the AI Tools Ecosystem.

## Test Categories

### 1. Individual Tool Tests

#### Telegram Tool Tests
```bash
# Test basic Telegram messaging (echo bot)
python3 src/tools/telegram/tests/test_echo.py

# Test AI integration with Telegram
python3 src/tools/telegram/tests/test_ai_integration.py
```

#### Ollama Tool Tests
```bash
# Test Ollama chat functionality
python3 src/tools/ollama/tests/test_chat.py
```

### 2. Integration Tests
The AI integration test (`test_ai_integration.py`) tests the full integration between Telegram and Ollama:
- Message reception from Telegram
- Processing through Ollama AI
- Response delivery back to Telegram

## Running Tests

### Prerequisites
1. Environment variables must be set:
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
2. Ollama must be running locally with the llama3.2 model installed

### Running All Tests
To run all tests in the project, use pytest:

```bash
# Run all tests
python3 -m pytest src/tools/

# Run tests with verbose output
python3 -m pytest -v src/tools/

# Run tests for a specific tool
python3 -m pytest src/tools/[tool_name]/tests/
```

### Running Individual Test Files
You can also run specific test files:

```bash
# Run a specific test file
python3 -m pytest src/tools/[tool_name]/tests/test_[feature].py
```

### Test Output
All test logs are stored in the `logs` directory:
- `logs/telegram_echo.log`: Basic Telegram messaging test logs
- `logs/ollama_test.log`: Ollama chat test logs
- `logs/telegram_ai.log`: Full AI integration test logs

## Test Structure
Each tool in the ecosystem follows a standard test structure:
```
tool_name/
└── tests/
    ├── __init__.py           # Test package initialization
    ├── test_base.py          # Tests for base functionality
    └── test_[feature].py     # Tests for specific features
```

## Writing Tests
1. Follow the template structure in `src/tools/templates/tests/`
2. Include both unit tests and integration tests
3. Use descriptive test names that explain what is being tested
4. Add docstrings to test classes and methods
5. Keep tests focused and independent
6. Use appropriate assertions and error messages

## Test Coverage
- Aim for comprehensive test coverage
- Test both success and failure cases
- Include edge cases and boundary conditions
- Test error handling and validation

## Continuous Integration
Tests are automatically run on:
- Pull requests
- Merges to main branch
- Release creation

## Adding New Tests
When adding new tests:
1. Place them in the appropriate tool's `tests` directory
2. Update this document with test running instructions
3. Add test documentation to the tool's README or docstring

## AI Model Testing

### Test Structure
All AI model tests should be placed in a `tests` directory within the relevant component:

```
src/
  tools/
    ai/
      tests/
        test_ai_model.py
```

### Testing AI Models

Test AI model implementations in `src/tools/ai/tests/`:

```python
import pytest
from src.tools.ai import AIModelFactory, Message, MessageRole

@pytest.fixture
async def ollama_model():
    model = AIModelFactory.create("ollama", model_name="llama2")
    await model.initialize()
    yield model
    await model.cleanup()

async def test_chat_response(ollama_model):
    response = await ollama_model.chat([
        Message(role=MessageRole.USER, content="Hello!")
    ])
    assert response.content
    assert response.model == "llama2"
    assert response.usage["total_tokens"] > 0

async def test_error_handling(ollama_model):
    with pytest.raises(Exception):
        await ollama_model.chat([])  # Empty messages should raise error
```

## Communications Agent Testing

### Test Structure
All Communications Agent tests should be placed in a `tests` directory within the relevant component:

```
src/
  agents/
    tests/
      test_communications_agent.py
```

### Testing Communications Agent

Test the Communications Agent in `src/agents/tests/`:

```python
import pytest
from src.agents import CommunicationsAgent
from src.tools.ai import Message

@pytest.fixture
async def agent():
    agent = CommunicationsAgent(ai_model_name="ollama")
    await agent.initialize()
    yield agent
    await agent.cleanup()

async def test_message_processing(agent):
    response = await agent.process_message(
        platform="telegram",
        user_id="test_user",
        message="Hello!"
    )
    assert response is not None
    assert isinstance(response, str)

async def test_conversation_history(agent):
    # Test that conversation history is maintained
    await agent.process_message("telegram", "user1", "Hello")
    await agent.process_message("telegram", "user1", "How are you?")
    
    history = agent.conversation_history["telegram:user1"]
    assert len(history) >= 3  # System + 2 user messages + responses
```

## Running AI Model and Communications Agent Tests

Use pytest to run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest src/agents/tests/test_communications_agent.py

# Run with coverage
pytest --cov=src
```

## Test Guidelines

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use fixtures for setup/teardown
3. **Mocking**: Mock external services when appropriate
4. **Coverage**: Aim for high test coverage
5. **Error Cases**: Test error conditions
6. **Async**: Use proper async/await patterns

## Mocking Examples

### Mock AI Model
```python
class MockAIModel:
    async def initialize(self):
        return True
        
    async def chat(self, messages, **kwargs):
        return ModelResponse(
            content="Mock response",
            model="mock",
            usage={"total_tokens": 10},
            raw_response={}
        )
        
    async def cleanup(self):
        pass
```

### Mock Communication Tool
```python
class MockCommunicationTool:
    def send_message(self, recipient, message):
        return True
        
    def receive_message(self, context):
        return {
            "user_id": "mock_user",
            "message": "Mock message"
        }
        
    def setup_channel(self, params):
        return True
```

## Integration Testing

For integration tests, create a separate directory:

```python
# tests/integration/test_agent_with_ai.py
async def test_agent_with_real_ai():
    agent = CommunicationsAgent(ai_model_name="ollama")
    await agent.initialize()
    
    try:
        response = await agent.process_message(
            "telegram", "test_user", "What's the weather?"
        )
        assert response is not None
    finally:
        await agent.cleanup()
```

## Performance Testing

Include performance tests for critical components:

```python
import time

async def test_agent_response_time():
    agent = CommunicationsAgent()
    await agent.initialize()
    
    start_time = time.time()
    await agent.process_message("telegram", "user", "Hello")
    duration = time.time() - start_time
    
    assert duration < 5.0  # Response should be under 5 seconds
