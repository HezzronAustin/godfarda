# AI Tools Ecosystem

A modular ecosystem of API-exposed tools designed for multi-AI agent interactions. This ecosystem provides a standardized way to create, register, and use tools through a RESTful API interface.

## 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Environment**
Create a `.env` file in the root directory:
```env
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
```

3. **Install Ollama**
Follow the [Ollama installation instructions](https://ollama.ai/download) for your platform.
Then pull the llama3.2 model:
```bash
ollama pull llama3.2
```

4. **Start Ollama Server**
```bash
ollama serve
```

## 🛠️ Running Services

We provide a convenient command-line interface to manage all services:

```bash
# Start the Telegram bot
./manage.py telegram

# Start the dashboard (default: http://127.0.0.1:8000)
./manage.py dashboard

# Start on a different host/port
./manage.py dashboard --host=0.0.0.0 --port=8080

# Start the Ollama server
./manage.py ollama
```

You can see all available commands by running:
```bash
./manage.py --help
```

## 🧪 Testing

We have several test suites available:

### Individual Tool Tests
```bash
# Test Telegram messaging (echo bot)
python3 src/tools/telegram/tests/test_echo.py

# Test Ollama chat
python3 src/tools/ollama/tests/test_chat.py
```

### Integration Tests
```bash
# Test Telegram-Ollama AI integration
python3 src/tools/telegram/tests/test_ai_integration.py
```

For detailed testing information, see [Testing Documentation](docs/TESTING.md)

## 📖 Documentation

- [Testing Guide](docs/TESTING.md)
- [Creating Tools](docs/creating_tools.md)
- [Tool Documentation](docs/tools/)

## 🛠 Available Tools

### Telegram Tools
Located in `src/tools/telegram/`:
- **TelegramMessageTool**: Send messages and receive updates from Telegram
- **TelegramHandler**: Handle messages with AI integration

### Ollama Tools
Located in `src/tools/ollama/`:
- **OllamaChatTool**: Interact with Ollama's chat models

## 🛠 Creating a New Tool

1. Create a new directory in `src/tools/` for your tool category
2. Create your tool class:

```python
from src.tools.templates.tool_template import BaseTool, ToolResponse

class MyTool(BaseTool):
    """Description of what your tool does."""
    
    def get_schema(self):
        return {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            },
            "param2": {
                "type": "integer",
                "description": "Parameter description"
            }
        }
    
    async def execute(self, params):
        # Implement your tool logic here
        result = do_something(params["param1"], params["param2"])
        return ToolResponse(success=True, data=result)
```

3. Add tests in a `tests` directory within your tool's directory
4. Update documentation:
   - Add tool documentation in `docs/tools/`
   - Update this README if adding a new category
   - Add testing information to `docs/TESTING.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for your changes
5. Update documentation
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
