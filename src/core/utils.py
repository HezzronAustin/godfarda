"""Core utilities for the AI Tools Ecosystem."""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
import json
import uuid

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def generate_request_id() -> str:
    """Generate a unique request ID for tracking tool/agent operations."""
    return str(uuid.uuid4())

def get_timestamp() -> str:
    """Get current ISO format timestamp."""
    return datetime.utcnow().isoformat()

def validate_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate data against a JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema to validate against
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        # Basic type validation - can be extended with full JSON schema validation
        for key, value_type in schema.items():
            if key not in data:
                return False, f"Missing required field: {key}"
            if not isinstance(data[key], value_type):
                return False, f"Invalid type for {key}: expected {value_type.__name__}"
        return True, None
    except Exception as e:
        return False, str(e)

class ToolException(Exception):
    """Base exception class for tool-related errors."""
    def __init__(self, message: str, tool_name: str, request_id: Optional[str] = None):
        self.message = message
        self.tool_name = tool_name
        self.request_id = request_id or generate_request_id()
        self.timestamp = get_timestamp()
        super().__init__(self.message)

class ValidationError(ToolException):
    """Raised when tool parameters fail validation."""
    pass

class ExecutionError(ToolException):
    """Raised when tool execution fails."""
    pass
