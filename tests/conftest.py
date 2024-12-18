import pytest
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.storage.database import Base, init_db
from src.rag.core import RAGSystem
from config.settings import Settings
import chromadb
from chromadb.config import Settings as ChromaSettings
import shutil

@pytest.fixture
def test_settings():
    test_dir = Path("./test_data")
    test_dir.mkdir(exist_ok=True)
    chroma_dir = test_dir / "chroma"
    chroma_dir.mkdir(exist_ok=True)
    
    return Settings(
        DATABASE_URL="sqlite:///test.db",
        CHROMA_PERSIST_DIR=chroma_dir
    )

@pytest.fixture
def db_engine(test_settings):
    # Create test database
    engine = create_engine(test_settings.DATABASE_URL)
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    engine.dispose()
    Base.metadata.drop_all(engine)
    try:
        if os.path.exists("test.db"):
            os.remove("test.db")
    except PermissionError:
        pass  # Ignore permission errors during cleanup

@pytest.fixture
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture(scope="function")
def chroma_client(test_settings):
    # Create test ChromaDB client with unique settings for each test
    test_dir = Path(f"./test_data/chroma_{os.getpid()}")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    settings = ChromaSettings(
        persist_directory=str(test_dir)
    )
    client = chromadb.Client(settings)
    
    yield client
    
    # Cleanup
    try:
        if test_dir.exists():
            shutil.rmtree(test_dir)
    except (PermissionError, OSError):
        pass  # Ignore cleanup errors

@pytest.fixture
def rag_system(db_engine, chroma_client):
    system = RAGSystem(db_engine, chroma_client)
    return system
