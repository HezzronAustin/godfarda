import asyncio
import logging
import os
from sqlalchemy import create_engine
from src.core.ConversationSystem import ConversationSystem
from src.storage.database import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Database setup
DB_FILE = "test_database.db"
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)  # Start with a fresh database for testing

# Create engine and initialize database
engine = create_engine(f"sqlite:///{DB_FILE}")
Base.metadata.create_all(engine)  # Create all tables

# Create conversation system
convo_system = ConversationSystem(engine=engine)

async def run_conversation():
    try:
        user_id = "12345"
        query = "What's the weather today?"

        print(f"\nUser: {query}")
        response = await convo_system.converse(query, user_id)
        print(f"Assistant: {response}\n")

        # Get and display conversation history
        history = await convo_system.get_conversation_history(user_id)
        print("Conversation History:")
        for msg in history:
            print(f"{msg.role}: {msg.content}")

    except Exception as e:
        print(f"Error during conversation: {str(e)}")
        logging.error("Error during conversation", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_conversation())