# Creating Tools

This guide explains how to create and register new tools in the AI Tools Ecosystem.

## Tool Structure

Each tool must inherit from `BaseTool` and implement two required methods:
- `get_schema()`: Defines the tool's parameter requirements
- `execute()`: Implements the tool's functionality

## Step-by-Step Guide

### 1. Create Tool Class

Create a new Python file in `src/tools/` directory:

```python
from typing import Dict, Any
from src.tools.templates.tool_template import BaseTool, ToolResponse
from src.core.utils import ValidationError

class MyCustomTool(BaseTool):
    """
    Detailed description of what your tool does.
    Include input/output specifications and any important notes.
    """
    
    def get_schema(self) -> Dict[str, Any]:
        """Define parameter requirements."""
        return {
            "required_param": str,
            "optional_param": int,  # Use type hints for validation
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        """Implement tool logic."""
        try:
            # Validate parameters
            if not self.validate_params(params):
                raise ValidationError(
                    "Invalid parameters provided",
                    self.name
                )
            
            # Implement your tool logic here
            result = await self._process_data(params)
            
            return ToolResponse(
                success=True,
                data=result
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e)
            )
    
    async def _process_data(self, params: Dict[str, Any]) -> Any:
        """
        Internal method for processing data.
        Break down complex logic into smaller, testable methods.
        """
        # Implementation here
        pass
```

### 2. Tool Configuration

If your tool needs configuration, create a JSON file in `config/`:

```json
{
    "tool_name": "MyCustomTool",
    "settings": {
        "timeout": 30,
        "max_retries": 3
    }
}
```

Access configuration in your tool:

```python
from src.core.config import ToolConfig

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.config = ToolConfig(self.name)
        self.timeout = self.config.get("timeout", 30)
```

### 3. Register the Tool

Register your tool in the registry:

```python
from src.core.registry import registry
registry.register_tool(MyCustomTool)
```

### 4. Error Handling

Use the provided exception classes for consistent error handling:

```python
from src.core.utils import ValidationError, ExecutionError

class MyCustomTool(BaseTool):
    async def execute(self, params):
        try:
            # Validation
            if not self.validate_params(params):
                raise ValidationError("Invalid parameters", self.name)
                
            # Execution
            if some_error_condition:
                raise ExecutionError("Processing failed", self.name)
                
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
```

## Best Practices

1. **Documentation**
   - Provide detailed docstrings
   - Document parameter requirements
   - Include usage examples

2. **Validation**
   - Always validate input parameters
   - Use type hints for better code clarity
   - Implement custom validation when needed

3. **Error Handling**
   - Use appropriate exception classes
   - Provide meaningful error messages
   - Handle all possible error cases

4. **Testing**
   - Write unit tests for your tool
   - Test both success and error cases
   - Test parameter validation

## Example Tool

Here's a complete example of a text analysis tool:

```python
from typing import Dict, Any
from src.tools.templates.tool_template import BaseTool, ToolResponse
from src.core.utils import ValidationError

class TextAnalyzer(BaseTool):
    """
    Analyzes text for various metrics including word count and sentiment.
    
    Parameters:
        text (str): Text to analyze
        analysis_type (str): Type of analysis ('word_count' or 'sentiment')
    
    Returns:
        ToolResponse with analysis results
    """
    
    def get_schema(self) -> Dict[str, Any]:
        return {
            "text": str,
            "analysis_type": str
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        try:
            if not self.validate_params(params):
                raise ValidationError("Invalid parameters", self.name)
            
            text = params["text"]
            analysis_type = params["analysis_type"]
            
            if analysis_type == "word_count":
                result = len(text.split())
            elif analysis_type == "sentiment":
                result = await self._analyze_sentiment(text)
            else:
                raise ValidationError(f"Unknown analysis type: {analysis_type}", self.name)
            
            return ToolResponse(
                success=True,
                data={
                    "analysis_type": analysis_type,
                    "result": result
                }
            )
            
        except Exception as e:
            return ToolResponse(success=False, error=str(e))
    
    async def _analyze_sentiment(self, text: str) -> str:
        # Simple sentiment analysis
        positive_words = {"good", "great", "excellent"}
        negative_words = {"bad", "poor", "terrible"}
        
        words = text.lower().split()
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        return "neutral"
```

## Testing Your Tool

Create tests in the `tests/tools/` directory:

```python
import pytest
from src.tools.text_analyzer import TextAnalyzer

@pytest.mark.asyncio
async def test_text_analyzer():
    tool = TextAnalyzer()
    
    # Test word count
    response = await tool.execute({
        "text": "Hello world",
        "analysis_type": "word_count"
    })
    assert response.success
    assert response.data["result"] == 2
    
    # Test sentiment
    response = await tool.execute({
        "text": "This is great",
        "analysis_type": "sentiment"
    })
    assert response.success
    assert response.data["result"] == "positive"
```
