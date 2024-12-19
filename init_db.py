from src.storage.database import init_db
from src.storage.database import session_scope
from src.storage.seeder import seed_all

import logging

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.info("Initializing database...")
    engine = init_db()
    with session_scope(engine) as session:
        seed_all(session)
    logging.info("Database initialized successfully!")
