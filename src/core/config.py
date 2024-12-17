"""Configuration management for the AI Tools Ecosystem."""

import os
from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Global settings for the AI Tools Ecosystem."""
    
    # API Settings
    API_VERSION: str = "v1"
    API_PREFIX: str = f"/api/{API_VERSION}"
    DEBUG: bool = False
    
    # Tool Settings
    TOOL_TIMEOUT: int = 30  # seconds
    MAX_CONCURRENT_TOOLS: int = 10
    
    # Agent Settings
    MAX_AGENTS: int = 5
    AGENT_TIMEOUT: int = 60  # seconds
    
    # Security Settings
    API_KEY_HEADER: str = "X-API-Key"
    REQUIRE_API_KEY: bool = False  # Changed to False for development
    
    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "development_db"
    DB_USER: str = "dev_user"
    DB_PASSWORD: str = "dev_password"
    
    # Server Settings
    PORT: int = 8000
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = 'allow'

# Global settings instance
settings = Settings()

class ToolConfig:
    """Configuration manager for individual tools."""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self._config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load tool-specific configuration."""
        config_path = os.path.join("config", f"{self.tool_name}.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self._config = dict(self._config, **json.load(f))
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
