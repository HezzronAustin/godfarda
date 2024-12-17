# Creating Agents

Agents are high-level components that orchestrate tools and provide specific functionality. This guide explains how to create new agents in the AI Tools Ecosystem.

## Agent Structure

All agents should be created in the `src/agents` directory and follow these guidelines:

1. Inherit from appropriate base classes when available
2. Implement clear interfaces for interaction
3. Include proper error handling and logging
4. Follow async/await patterns for non-blocking operations

## Available Agents

### Communications Agent

The Communications Agent orchestrates messaging tasks across multiple platforms while leveraging AI capabilities for message processing.

#### Features
- Platform-agnostic messaging interface
- Integrated AI processing with conversation history
- Pluggable communication tools (e.g., Telegram, Slack)
- Modular AI model system for easy switching between different AI providers

#### Usage Example
```python
from src.agents import CommunicationsAgent

# Create agent with specific AI model
agent = CommunicationsAgent(
    ai_model_name="ollama",
    ai_model_params={"model_name": "llama2"}
)

# Initialize the agent
await agent.initialize()

# Handle incoming message
success = await agent.handle_incoming_message(
    platform="telegram",
    context={"user_id": "123", "message": "Hello!"}
)

# Clean up
await agent.cleanup()
```

#### Adding New Communication Tools
1. Implement the `CommunicationTool` interface:
```python
class CustomPlatformTool(CommunicationTool):
    async def send_message(self, recipient: str, message: str) -> bool:
        # Implementation
        pass

    async def receive_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        pass

    async def setup_channel(self, params: Dict[str, Any]) -> bool:
        # Implementation
        pass
```

2. Register the tool with the agent:
```python
agent.register_tool("custom_platform", CustomPlatformTool())
```

### Text Agent

Agents are classes that inherit from `BaseAgent` and implement two required methods:
- `initialize()`: Set up the agent and load required tools
- `process()`: Process input data using available tools

## Step-by-Step Guide

### 1. Create Agent Class

Create a new Python file in `src/agents/` directory:

```python
from typing import Dict, Any
from src.agents.templates.agent_template import BaseAgent, AgentConfig
from src.core.utils import ExecutionError

class MyCustomAgent(BaseAgent):
    """
    Detailed description of what your agent does.
    Include capabilities and required tools.
    """
    
    async def initialize(self) -> bool:
        """
        Initialize the agent and load required tools.
        Returns True if initialization is successful.
        """
        try:
            # Load required tools
            tool_names = self.config.allowed_tools
            for tool_name in tool_names:
                tool_class = registry.get_tool(tool_name)
                if not tool_class:
                    raise ExecutionError(f"Required tool not found: {tool_name}", self.name)
                self.tools[tool_name] = tool_class()
            
            return True
            
        except Exception as e:
            logging.error(f"Agent initialization failed: {str(e)}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process input data using available tools.
        """
        try:
            # Validate input
            if not self._validate_input(input_data):
                raise ValidationError("Invalid input data", self.name)
            
            # Use tools to process data
            result = await self._process_with_tools(input_data)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_with_tools(self, data: Dict[str, Any]) -> Any:
        """
        Internal method for processing data with tools.
        """
        # Example: Use a text analysis tool
        text_result = await self.use_tool("TextAnalyzer", {
            "text": data["input_text"],
            "analysis_type": "sentiment"
        })
        
        if not text_result.success:
            raise ExecutionError(f"Text analysis failed: {text_result.error}", self.name)
        
        return text_result.data
```

### 2. Agent Configuration

Create an agent configuration:

```python
config = AgentConfig(
    name="MyCustomAgent",
    allowed_tools=["TextAnalyzer", "ImageProcessor"],
    parameters={
        "max_retries": 3,
        "timeout": 30
    }
)

agent = MyCustomAgent(config)
```

### 3. Register the Agent

Register your agent in the registry:

```python
from src.core.registry import registry
registry.register_agent(MyCustomAgent)
```

## Using Tools in Agents

Agents can use tools through the `use_tool` method:

```python
class MyCustomAgent(BaseAgent):
    async def process(self, input_data):
        # Sequential tool usage
        text_result = await self.use_tool("TextAnalyzer", {
            "text": input_data["text"],
            "analysis_type": "sentiment"
        })
        
        if text_result.success:
            # Use another tool with the results
            summary_result = await self.use_tool("TextSummarizer", {
                "text": input_data["text"],
                "sentiment": text_result.data["result"]
            })
            return summary_result.data
```

## Best Practices

1. **Modularity**: Design agents to be modular and extensible
2. **Error Handling**: Include comprehensive error handling
3. **Documentation**: Provide clear documentation and examples
4. **Testing**: Include unit tests for all functionality
5. **Logging**: Add appropriate logging for debugging
6. **Configuration**: Use configuration files for customizable parameters

## Testing

Refer to [TESTING.md](TESTING.md) for information about testing agents.

## Example Agent

Here's a complete example of a text processing agent:

```python
from typing import Dict, Any
from src.agents.templates.agent_template import BaseAgent
from src.core.utils import ValidationError, ExecutionError

class TextProcessingAgent(BaseAgent):
    """
    An agent that processes text using various analysis tools.
    
    Required Tools:
    - TextAnalyzer
    - TextSummarizer
    """
    
    async def initialize(self) -> bool:
        required_tools = ["TextAnalyzer", "TextSummarizer"]
        
        try:
            for tool_name in required_tools:
                if tool_name not in self.config.allowed_tools:
                    raise ExecutionError(
                        f"Required tool {tool_name} not allowed",
                        self.name
                    )
                
                tool_class = registry.get_tool(tool_name)
                if not tool_class:
                    raise ExecutionError(
                        f"Required tool {tool_name} not found",
                        self.name
                    )
                    
                self.tools[tool_name] = tool_class()
            
            return True
            
        except Exception as e:
            logging.error(f"Initialization failed: {str(e)}")
            return False
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if "text" not in input_data:
                raise ValidationError("Input must contain 'text' field", self.name)
            
            # Analyze sentiment
            sentiment_result = await self.use_tool("TextAnalyzer", {
                "text": input_data["text"],
                "analysis_type": "sentiment"
            })
            
            if not sentiment_result.success:
                raise ExecutionError(
                    f"Sentiment analysis failed: {sentiment_result.error}",
                    self.name
                )
            
            # Generate summary
            summary_result = await self.use_tool("TextSummarizer", {
                "text": input_data["text"],
                "max_length": input_data.get("max_length", 100)
            })
            
            if not summary_result.success:
                raise ExecutionError(
                    f"Summarization failed: {summary_result.error}",
                    self.name
                )
            
            return {
                "success": True,
                "sentiment": sentiment_result.data["result"],
                "summary": summary_result.data["summary"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

## Testing Your Agent

Create tests in the `tests/agents/` directory:

```python
import pytest
from src.agents.text_processing_agent import TextProcessingAgent
from src.agents.templates.agent_template import AgentConfig

@pytest.mark.asyncio
async def test_text_processing_agent():
    config = AgentConfig(
        name="TestAgent",
        allowed_tools=["TextAnalyzer", "TextSummarizer"]
    )
    
    agent = TextProcessingAgent(config)
    assert await agent.initialize()
    
    result = await agent.process({
        "text": "This is a great test message that needs to be analyzed.",
        "max_length": 50
    })
    
    assert result["success"]
    assert "sentiment" in result
    assert "summary" in result
