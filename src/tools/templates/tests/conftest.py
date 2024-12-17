"""Pytest configuration for tool tests."""

import os
import logging
import pytest
from typing import Generator
from ..utils.logging import setup_logger


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging() -> Generator[None, None, None]:
    """Set up logging for tests.
    
    This fixture runs automatically for all tests in the session.
    It sets up logging and ensures the logs directory exists.
    """
    # Get the test directory path
    test_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(test_dir, 'logs', 'test.log')
    
    # Set up logger
    logger = setup_logger(
        name='tool_test',
        log_file=log_file,
        level=logging.DEBUG
    )
    
    yield
    
    # Clean up handlers to avoid duplicate logs
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
