import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.storage.database import init_db
from config.settings import settings
import chromadb
from chromadb.config import Settings as ChromaSettings

def main():
    # Initialize SQLite database
    print("Initializing SQLite database...")
    engine = init_db(settings.DATABASE_URL)
    
    # Initialize ChromaDB
    print("Initializing ChromaDB...")
    chroma_settings = ChromaSettings(
        persist_directory=str(settings.CHROMA_PERSIST_DIR)
    )
    client = chromadb.Client(chroma_settings)
    
    # Create default collection
    try:
        collection = client.create_collection(
            name="godfarda_docs",
            metadata={"hnsw:space": "cosine"}
        )
        print("Created ChromaDB collection 'godfarda_docs'")
    except ValueError:
        print("Collection 'godfarda_docs' already exists")
    
    print("Initialization complete!")

if __name__ == "__main__":
    main()
