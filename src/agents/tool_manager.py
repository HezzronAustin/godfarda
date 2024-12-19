from typing import Dict, Any, Optional, Callable
import logging
from src.agents.loader import FunctionLoader, LoadedFunction, FunctionLoadError
from src.agents.models import Tool

logger = logging.getLogger(__name__)

class ToolManager:
    """Manages tool loading and execution for agents"""
    
    @staticmethod
    def load_tool_implementation(tool: Tool) -> Optional[LoadedFunction]:
        """Load a tool's implementation from either code or file
        
        Args:
            tool: Tool model instance
            
        Returns:
            LoadedFunction if successful, None if no implementation found
            
        Raises:
            FunctionLoadError: If implementation cannot be loaded
        """
        try:
            if tool.implementation:
                logger.debug(f"Loading tool {tool.name} from stored code")
                return FunctionLoader.load_from_code(tool.implementation, tool.name)
                
            elif tool.implementation_path:
                logger.debug(f"Loading tool {tool.name} from file: {tool.implementation_path}")
                return FunctionLoader.load_from_file(tool.implementation_path, tool.name)
                
            else:
                logger.warning(f"No implementation found for tool {tool.name}")
                return None
                
        except FunctionLoadError as e:
            logger.error(f"Error loading tool {tool.name}: {str(e)}")
            raise
            
    @staticmethod
    def load_tools(tools: list[Tool]) -> Dict[str, LoadedFunction]:
        """Load implementations for multiple tools
        
        Args:
            tools: List of Tool model instances
            
        Returns:
            Dictionary mapping tool names to their loaded implementations
        """
        loaded_tools = {}
        for tool in tools:
            try:
                if implementation := ToolManager.load_tool_implementation(tool):
                    loaded_tools[tool.name] = implementation
            except FunctionLoadError as e:
                logger.error(f"Skipping tool {tool.name} due to load error: {str(e)}")
                continue
        return loaded_tools
        
    @staticmethod
    def create_tool_function(loaded_func: LoadedFunction, tool: Tool) -> Callable:
        """Create a wrapped function that includes tool configuration
        
        Args:
            loaded_func: LoadedFunction instance
            tool: Tool model instance
            
        Returns:
            Wrapped function with tool configuration
        """
        def tool_wrapper(*args, **kwargs):
            # Add tool configuration to kwargs if specified
            if tool.config_data:
                kwargs['tool_config'] = tool.config_data
            if tool.parameters:
                kwargs['parameters'] = tool.parameters
                
            return loaded_func.func(*args, **kwargs)
            
        # Copy metadata from original function
        tool_wrapper.__name__ = loaded_func.name
        tool_wrapper.__doc__ = loaded_func.doc or tool.description
        
        return tool_wrapper
