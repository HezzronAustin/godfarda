"""Test cases for the base module."""

import logging
import pytest
from typing import Any, Dict

from ..base import BaseToolTemplate
from ..utils.logging import setup_logger

# Set up logger for this test module
logger = logging.getLogger(__name__)


class TestToolTemplate(BaseToolTemplate):
    """Test implementation of BaseToolTemplate."""

    def initialize(self) -> bool:
        logger.info("Initializing test tool")
        return True

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        logger.info(f"Executing test tool with args: {args}, kwargs: {kwargs}")
        return True

    def cleanup(self) -> None:
        logger.info("Cleaning up test tool")
        pass


class TestBaseToolTemplate:
    """Test cases for BaseToolTemplate."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test cases."""
        self.tool = TestToolTemplate(
            name="TestTool",
            description="Test tool implementation",
            config={"test_key": "test_value"}
        )
        logger.info(f"Created test tool: {self.tool}")

    def test_initialization(self):
        """Test tool initialization."""
        logger.info("Testing tool initialization")
        assert self.tool.name == "TestTool"
        assert self.tool.description == "Test tool implementation"
        assert isinstance(self.tool.config, Dict)
        assert self.tool.config["test_key"] == "test_value"

    def test_validate_config(self):
        """Test configuration validation."""
        logger.info("Testing config validation")
        assert self.tool.validate_config()

    def test_string_representation(self):
        """Test string representation of the tool."""
        logger.info("Testing string representation")
        expected = "TestTool: Test tool implementation"
        assert str(self.tool) == expected


if __name__ == '__main__':
    setup_logger()
    pytest.main()
