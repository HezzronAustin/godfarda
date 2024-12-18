import os
from pathlib import Path
from typing import Dict, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base paths
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    
    # Database
    DATABASE_URL: str = "sqlite:///godfarda.db"
    
    # ChromaDB
    CHROMA_PERSIST_DIR: Path = DATA_DIR / "chroma"
    
    # Agent settings
    MAX_AGENT_DEPTH: int = 5
    DEFAULT_AGENT_CAPABILITIES: list = ["text_analysis", "code_search"]
    
    # RAG settings
    DEFAULT_CHUNK_SIZE: int = 1000
    DEFAULT_CHUNK_OVERLAP: int = 200
    MAX_CONTEXT_DOCUMENTS: int = 5
    
    # Tool settings
    TOOL_TIMEOUT_SECONDS: int = 30
    MAX_CONCURRENT_TOOLS: int = 10
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        
        # Create necessary directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.CHROMA_PERSIST_DIR.mkdir(exist_ok=True)
        
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
