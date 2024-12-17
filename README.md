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
DEBUG=True
REQUIRE_API_KEY=True
API_KEY=your-secret-key
```

3. **Run the API**
```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000/api/v1/`

## 📖 Documentation

- [Creating Tools](docs/creating_tools.md)
- [Creating Agents](docs/creating_agents.md)
- [API Reference](docs/api_reference.md)
- [Configuration Guide](docs/configuration.md)

## 🛠 Creating a New Tool

1. Create a new file in `src/tools/`:

```python
from src.tools.templates.tool_template import BaseTool, ToolResponse

class MyTool(BaseTool):
    """Description of what your tool does."""
    
    def get_schema(self):
        return {
            "param1": str,
            "param2": int
        }
    
    async def execute(self, params):
        # Implement your tool logic here
        result = do_something(params["param1"], params["param2"])
        return ToolResponse(success=True, data=result)
```

2. Register your tool:

```python
from src.core.registry import registry
registry.register_tool(MyTool)
```

## 🤖 Creating a New Agent

1. Create a new file in `src/agents/`:

```python
from src.agents.templates.agent_template import BaseAgent

class MyAgent(BaseAgent):
    """Description of what your agent does."""
    
    async def initialize(self):
        # Set up your agent
        return True
    
    async def process(self, input_data):
        # Process input using tools
        result = await self.use_tool("MyTool", {
            "param1": "value",
            "param2": 42
        })
        return result
```

2. Register your agent:

```python
from src.core.registry import registry
registry.register_agent(MyAgent)
```

## 🌐 API Usage

### Execute a Tool
```bash
curl -X POST "http://localhost:8000/api/v1/tools/MyTool" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
           "parameters": {
             "param1": "value",
             "param2": 42
           }
         }'
```

### Use an Agent
```bash
curl -X POST "http://localhost:8000/api/v1/agents/MyAgent" \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{
           "input_data": {
             "key": "value"
           }
         }'
```

## 📝 Example Tool

Check out the `TextAnalyzer` tool in `src/tools/text_analyzer.py` for a complete example implementation.

## 🔧 Configuration

The ecosystem is configurable through:
- Environment variables
- `.env` file
- Tool-specific configuration files in `config/`

See [Configuration Guide](docs/configuration.md) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📜 License

MIT License - see LICENSE file for details
