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
