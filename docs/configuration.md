# Configuration Guide

This guide explains how to configure the AI Tools Ecosystem at various levels.

## Environment Configuration

The ecosystem uses environment variables for global configuration. These can be set in a `.env` file:

```env
# API Settings
DEBUG=True
API_VERSION=v1
API_PREFIX=/api/v1

# Security
REQUIRE_API_KEY=True
API_KEY=your-secret-key

# Tool Settings
TOOL_TIMEOUT=30
MAX_CONCURRENT_TOOLS=10

# Agent Settings
MAX_AGENTS=5
AGENT_TIMEOUT=60
```

## Configuration Hierarchy

The configuration system follows this hierarchy (later ones override earlier ones):
1. Default values in code
2. Environment variables
3. `.env` file
4. Tool/Agent specific config files

## Global Settings

Global settings are managed through the `Settings` class in `src/core/config.py`:

```python
from src.core.config import settings

# Access settings
debug_mode = settings.DEBUG
api_version = settings.API_VERSION
```

## Tool Configuration

### Tool-Specific Config Files

Create JSON configuration files in the `config/` directory:

```json
// config/text_analyzer.json
{
    "timeout": 30,
    "max_retries": 3,
    "cache_results": true,
    "parameters": {
        "max_text_length": 1000,
        "supported_languages": ["en", "es", "fr"]
    }
}
```

### Using Tool Configuration

Access tool configuration in your tool implementation:

```python
from src.core.config import ToolConfig

class MyTool(BaseTool):
    def __init__(self):
        super().__init__()
        self.config = ToolConfig(self.name)
        
        # Access configuration values
        self.timeout = self.config.get("timeout", 30)
        self.max_retries = self.config.get("max_retries", 3)
```

## Agent Configuration

### Agent Config Model

Agents are configured using the `AgentConfig` model:

```python
from src.agents.templates.agent_template import AgentConfig

config = AgentConfig(
    name="MyAgent",
    allowed_tools=["TextAnalyzer", "ImageProcessor"],
    parameters={
        "max_retries": 3,
        "timeout": 30
    }
)
```

### Agent-Specific Settings

Create JSON configuration files for agents:

```json
// config/text_processor_agent.json
{
    "allowed_tools": ["TextAnalyzer", "TextSummarizer"],
    "parameters": {
        "max_concurrent_tools": 2,
        "timeout": 60,
        "retry_delay": 5
    }
}
```

## Advanced Configuration

### Custom Configuration Providers

You can implement custom configuration providers:

```python
from typing import Any, Dict
from abc import ABC, abstractmethod

class ConfigProvider(ABC):
    @abstractmethod
    def get_config(self, name: str) -> Dict[str, Any]:
        pass

class RedisConfigProvider(ConfigProvider):
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
    
    def get_config(self, name: str) -> Dict[str, Any]:
        config_data = self.redis_client.get(f"config:{name}")
        return json.loads(config_data) if config_data else {}
```

### Dynamic Configuration

Implement dynamic configuration updates:

```python
class DynamicToolConfig:
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self._config = {}
        self._last_update = 0
        self._update_interval = 60  # seconds
    
    def get(self, key: str, default: Any = None) -> Any:
        self._maybe_update()
        return self._config.get(key, default)
    
    def _maybe_update(self):
        now = time.time()
        if now - self._last_update > self._update_interval:
            self._config = self._load_config()
            self._last_update = now
```

## Security

### API Key Configuration

Configure API key validation:

```python
# In .env
REQUIRE_API_KEY=True
API_KEY=your-secret-key
API_KEY_HEADER=X-API-Key

# In code
from src.core.config import settings

async def verify_api_key(api_key: str) -> bool:
    if not settings.REQUIRE_API_KEY:
        return True
    return api_key == settings.API_KEY
```

### Tool Access Control

Configure tool access permissions:

```python
# config/tool_permissions.json
{
    "TextAnalyzer": {
        "required_role": "analyst",
        "rate_limit": 100
    },
    "ImageProcessor": {
        "required_role": "admin",
        "rate_limit": 50
    }
}
```

## Logging Configuration

Configure logging settings:

```python
# In .env
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# In code
import logging
from src.core.config import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
```

## Development vs Production

Use different configurations for development and production:

```env
# .env.development
DEBUG=True
REQUIRE_API_KEY=False

# .env.production
DEBUG=False
REQUIRE_API_KEY=True
API_KEY=secure-key
```

Load the appropriate configuration:

```python
import os
from dotenv import load_dotenv

env = os.getenv("ENVIRONMENT", "development")
load_dotenv(f".env.{env}")
```

## Best Practices

1. **Security**
   - Never commit sensitive configuration to version control
   - Use environment variables for secrets
   - Implement proper access control

2. **Maintenance**
   - Keep configuration DRY (Don't Repeat Yourself)
   - Document all configuration options
   - Use type hints and validation

3. **Performance**
   - Cache configuration where appropriate
   - Implement efficient updates
   - Monitor configuration usage

4. **Testing**
   - Create test configurations
   - Mock configuration in tests
   - Validate configuration changes
