import os
import inspect
import logging
import importlib.util
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class LoadedFunction:
    """Container for loaded function and its metadata"""
    func: Callable
    name: str
    source_path: Optional[str] = None
    is_async: bool = False
    doc: Optional[str] = None

class FunctionLoadError(Exception):
    """Base exception for function loading errors"""
    pass

class FunctionLoader:
    """Utility class for dynamically loading functions"""
    
    @staticmethod
    def load_from_file(file_path: str, function_name: str) -> LoadedFunction:
        """Load a specific function from a Python file
        
        Args:
            file_path: Path to the Python file
            function_name: Name of the function to load
            
        Returns:
            LoadedFunction object containing the loaded function and metadata
            
        Raises:
            FunctionLoadError: If function cannot be loaded
        """
        try:
            # Ensure file exists
            if not os.path.exists(file_path):
                raise FunctionLoadError(f"File not found: {file_path}")
                
            # Get module name from file path
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Load module spec and create module
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if not spec or not spec.loader:
                raise FunctionLoadError(f"Could not load module spec from {file_path}")
                
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get function from module
            if not hasattr(module, function_name):
                raise FunctionLoadError(f"Function {function_name} not found in {file_path}")
                
            func = getattr(module, function_name)
            
            # Check if function is async
            is_async = inspect.iscoroutinefunction(func)
            
            return LoadedFunction(
                func=func,
                name=function_name,
                source_path=file_path,
                is_async=is_async,
                doc=func.__doc__
            )
            
        except Exception as e:
            logger.error(f"Error loading function {function_name} from {file_path}: {str(e)}")
            raise FunctionLoadError(f"Failed to load function: {str(e)}") from e
    
    @staticmethod
    def load_from_code(code: str, function_name: str) -> LoadedFunction:
        """Create a function from a code string
        
        Args:
            code: String containing Python code
            function_name: Name of the function to extract
            
        Returns:
            LoadedFunction object containing the created function and metadata
            
        Raises:
            FunctionLoadError: If function cannot be created
        """
        try:
            # Create namespace for function
            namespace = {}
            
            # Execute code in namespace
            exec(code, namespace)
            
            # Get function from namespace
            if function_name not in namespace:
                raise FunctionLoadError(f"Function {function_name} not found in code")
                
            func = namespace[function_name]
            
            # Verify it's actually a function
            if not callable(func):
                raise FunctionLoadError(f"{function_name} is not a callable function")
                
            # Check if async
            is_async = inspect.iscoroutinefunction(func)
            
            return LoadedFunction(
                func=func,
                name=function_name,
                is_async=is_async,
                doc=func.__doc__
            )
            
        except Exception as e:
            logger.error(f"Error creating function {function_name} from code: {str(e)}")
            raise FunctionLoadError(f"Failed to create function: {str(e)}") from e
    
    @staticmethod
    def load_from_directory(directory: str, recursive: bool = True) -> Dict[str, LoadedFunction]:
        """Load all functions from Python files in a directory
        
        Args:
            directory: Path to directory containing Python files
            recursive: Whether to search subdirectories
            
        Returns:
            Dictionary mapping function names to LoadedFunction objects
            
        Raises:
            FunctionLoadError: If directory cannot be processed
        """
        try:
            functions = {}
            directory_path = Path(directory)
            
            if not directory_path.exists():
                raise FunctionLoadError(f"Directory not found: {directory}")
                
            # Get all Python files
            pattern = '**/*.py' if recursive else '*.py'
            for file_path in directory_path.glob(pattern):
                try:
                    # Skip __init__.py files
                    if file_path.name == '__init__.py':
                        continue
                        
                    # Load module
                    spec = importlib.util.spec_from_file_location(
                        file_path.stem, str(file_path)
                    )
                    if not spec or not spec.loader:
                        logger.warning(f"Could not load module spec from {file_path}")
                        continue
                        
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Get all functions
                    for name, obj in inspect.getmembers(module, inspect.isfunction):
                        if name.startswith('_'):  # Skip private functions
                            continue
                            
                        functions[name] = LoadedFunction(
                            func=obj,
                            name=name,
                            source_path=str(file_path),
                            is_async=inspect.iscoroutinefunction(obj),
                            doc=obj.__doc__
                        )
                        
                except Exception as e:
                    logger.warning(f"Error processing file {file_path}: {str(e)}")
                    continue
                    
            return functions
            
        except Exception as e:
            logger.error(f"Error loading functions from directory {directory}: {str(e)}")
            raise FunctionLoadError(f"Failed to load directory: {str(e)}") from e
