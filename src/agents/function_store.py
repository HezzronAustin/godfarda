from typing import Dict, Any, Optional, Callable, Union
import ast
import inspect
import asyncio
from functools import wraps
import hashlib
import json
from sqlalchemy.orm import Session
from .models import Function
from pydantic import BaseModel, ValidationError

class FunctionMetadata(BaseModel):
    """Metadata for stored functions"""
    version: str
    hash: str
    is_async: bool
    requires_context: bool
    allowed_imports: list[str]
    memory_limit: int = 512  # MB
    timeout: int = 30  # seconds
    safe_mode: bool = True

class FunctionStore:
    """Manages storage and execution of database-stored functions"""
    
    def __init__(self, session: Session):
        self.session = session
        self._function_cache: Dict[str, Callable] = {}
        self._metadata_cache: Dict[str, FunctionMetadata] = {}
        
        # Allowed built-in functions and modules for safe mode
        self.ALLOWED_BUILTINS = {
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set',
            'tuple', 'sum', 'min', 'max', 'sorted', 'enumerate', 'zip',
            'round', 'abs', 'all', 'any', 'filter', 'map'
        }
        
        self.ALLOWED_IMPORTS = {
            'json', 'datetime', 'math', 'statistics', 're', 'collections',
            'itertools', 'functools', 'typing'
        }
    
    def _validate_code(self, code: str) -> None:
        """Validate Python code for security"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {e}")
        
        for node in ast.walk(tree):
            # Check for dangerous built-ins
            if isinstance(node, ast.Name) and node.id not in self.ALLOWED_BUILTINS:
                if node.id in __builtins__:
                    raise ValueError(f"Use of restricted built-in: {node.id}")
            
            # Check for imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = node.names[0].name.split('.')[0]
                if module not in self.ALLOWED_IMPORTS:
                    raise ValueError(f"Import of restricted module: {module}")
            
            # Check for dangerous operations
            if isinstance(node, (ast.Execute, ast.Eval)):
                raise ValueError("Execute/Eval statements are not allowed")
    
    def _compute_hash(self, code: str) -> str:
        """Compute hash of function code"""
        return hashlib.sha256(code.encode()).hexdigest()
    
    def _create_metadata(self, code: str, is_async: bool) -> FunctionMetadata:
        """Create metadata for a function"""
        return FunctionMetadata(
            version="1.0",
            hash=self._compute_hash(code),
            is_async=is_async,
            requires_context=False,
            allowed_imports=list(self.ALLOWED_IMPORTS),
            memory_limit=512,
            timeout=30,
            safe_mode=True
        )
    
    async def store_function(self,
                           name: str,
                           code: str,
                           description: str,
                           input_schema: Dict[str, Any],
                           output_schema: Dict[str, Any],
                           is_async: bool = True,
                           metadata: Optional[Dict[str, Any]] = None) -> Function:
        """Store a function in the database"""
        # Validate the code
        self._validate_code(code)
        
        # Create metadata
        func_metadata = self._create_metadata(code, is_async)
        
        # Create or update function
        function = self.session.query(Function).filter_by(name=name).first()
        if function is None:
            function = Function(
                name=name,
                description=description,
                python_code=code,
                input_schema=input_schema,
                output_schema=output_schema,
                is_async=is_async,
                metadata={
                    **func_metadata.dict(),
                    **(metadata or {})
                }
            )
            self.session.add(function)
        else:
            function.python_code = code
            function.description = description
            function.input_schema = input_schema
            function.output_schema = output_schema
            function.is_async = is_async
            function.metadata = {
                **func_metadata.dict(),
                **(metadata or {})
            }
        
        self.session.commit()
        
        # Clear cache for this function
        if name in self._function_cache:
            del self._function_cache[name]
        if name in self._metadata_cache:
            del self._metadata_cache[name]
        
        return function
    
    def _load_function(self, function: Function) -> Callable:
        """Load a function from its stored code"""
        # Create a restricted globals dictionary
        restricted_globals = {
            '__builtins__': {name: __builtins__[name] for name in self.ALLOWED_BUILTINS}
        }
        
        # Execute the code in a restricted environment
        try:
            exec(function.python_code, restricted_globals)
        except Exception as e:
            raise ValueError(f"Error loading function: {e}")
        
        # Get the function object
        func = restricted_globals.get(function.name)
        if not func or not callable(func):
            raise ValueError("Function not found in code")
        
        return func
    
    async def get_function(self, name: str) -> Callable:
        """Get a function by name"""
        # Check cache first
        if name in self._function_cache:
            return self._function_cache[name]
        
        # Get from database
        function = self.session.query(Function).filter_by(name=name).first()
        if function is None:
            raise ValueError(f"Function {name} not found")
        
        # Load the function
        func = self._load_function(function)
        
        # Cache the function
        self._function_cache[name] = func
        self._metadata_cache[name] = FunctionMetadata(**function.metadata)
        
        return func
    
    async def execute_function(self,
                             name: str,
                             *args,
                             timeout: Optional[int] = None,
                             **kwargs) -> Any:
        """Execute a stored function with safety measures"""
        # Get the function
        func = await self.get_function(name)
        metadata = self._metadata_cache[name]
        
        # Set timeout
        timeout = timeout or metadata.timeout
        
        # Execute the function
        try:
            if metadata.is_async:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, *args, **kwargs),
                    timeout
                )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Function {name} exceeded timeout of {timeout} seconds")
        except Exception as e:
            raise RuntimeError(f"Error executing function {name}: {e}")
    
    def clear_cache(self):
        """Clear the function cache"""
        self._function_cache.clear()
        self._metadata_cache.clear()
