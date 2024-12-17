"""
Telegram Tool Package

This package provides tools for interacting with the Telegram Bot API.

Components:
    - TelegramMessageTool: For sending messages and receiving updates
    - TelegramHandler: For handling messages with AI integration

Testing:
    Run individual tests:
    ```bash
    # Test basic messaging (echo bot)
    python3 src/tools/telegram/tests/test_echo.py

    # Test AI integration
    python3 src/tools/telegram/tests/test_ai_integration.py
    ```

    For full testing documentation, see docs/TESTING.md
"""

from .message import TelegramMessageTool
from .handler import TelegramHandler

__all__ = ['TelegramMessageTool', 'TelegramHandler']
