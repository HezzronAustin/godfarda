import os
from sqlalchemy import create_engine
from src.agents.models import Base
from src.storage.database import init_db, session_scope

def migrate_database():
    """Migrate the database to the latest schema."""
    try:
        # Initialize database with new schema
        engine = init_db()
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        print("Database migration completed successfully!")
        return engine
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        raise

if __name__ == "__main__":
    migrate_database()
