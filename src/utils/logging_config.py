import logging
import logging.handlers
import os
from datetime import datetime

def setup_logging(log_dir: str = "logs"):
    """Set up logging configuration for the entire application."""
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # Generate log filenames with timestamps
    timestamp = datetime.now().strftime("%Y%m%d")
    general_log = os.path.join(log_dir, f"godfarda_{timestamp}.log")
    error_log = os.path.join(log_dir, f"godfarda_error_{timestamp}.log")
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    error_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
        'Exception:\n%(exc_info)s'
    )
    
    # Set up handlers
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(detailed_formatter)
    
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        general_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # File handler for errors
    error_handler = logging.handlers.RotatingFileHandler(
        error_log,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(error_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # Add handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure module loggers
    loggers = [
        'telegram_bot',
        'ai.core',
        'agents.factory',
        'agents.registry',
        'agents.function_store'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        # Don't propagate to root logger since we're setting explicit handlers
        logger.propagate = False
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        logger.addHandler(error_handler)
    
    # Log startup message
    root_logger.info("Logging system initialized")
