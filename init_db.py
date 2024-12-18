from src.storage.database import init_db
import logging

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Initializing database...")
    engine = init_db()
    logging.info("Database initialized successfully!")
