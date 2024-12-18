from typing import Dict, Any, Callable
import logging

logger = logging.getLogger('agents.function_store')

class FunctionStore:
    def __init__(self):
        self._functions: Dict[str, Callable] = {}
        
    def register(self, name: str, func: Callable) -> None:
        """Register a function"""
        if name in self._functions:
            logger.warning(f"Function {name} already registered, overwriting")
        self._functions[name] = func
        
    def get(self, name: str) -> Callable:
        """Get a function by name"""
        if name not in self._functions:
            raise ValueError(f"Function {name} not found")
        return self._functions[name]
        
    def list_functions(self) -> list[str]:
        """List all registered functions"""
        return list(self._functions.keys())
