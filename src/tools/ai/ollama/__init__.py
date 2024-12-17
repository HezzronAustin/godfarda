"""
Ollama Tool Package

This package provides tools for interacting with the Ollama API.

Components:
    - OllamaChatTool: For sending messages to and receiving responses from Ollama models

Testing:
    Run the chat test:
    ```bash
    # Test Ollama chat functionality
    python3 src/tools/ollama/tests/test_chat.py
    ```

    For full testing documentation, see docs/TESTING.md
"""

from .chat import OllamaChatTool

__all__ = ['OllamaChatTool']
