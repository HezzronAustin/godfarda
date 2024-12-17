"""Tool Template Package

This package provides template files and structure for creating new tools in the AI Tools Ecosystem.

Components:
    - base.py: Base classes and core functionality
    - main.py: Main tool implementation
    - tests/: Test directory with unit and integration tests

Usage:
    1. Copy this template directory to create a new tool
    2. Rename files and modify contents according to your tool's needs
    3. Implement your tool's specific functionality
    4. Add comprehensive tests

For detailed documentation on creating new tools, see the README.md file.
"""

from .base import BaseToolTemplate  # noqa: F401
from .main import ToolTemplate  # noqa: F401

__all__ = ['BaseToolTemplate', 'ToolTemplate']
