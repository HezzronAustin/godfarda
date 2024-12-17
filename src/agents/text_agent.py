"""Text analysis agent implementation."""

from typing import Dict, Any, Optional
from src.agents.base import BaseAgent, AgentConfig
from src.core.utils import ValidationError

class TextAgent(BaseAgent):
    """A simple agent that uses the text analyzer tool."""
    
    async def initialize(self) -> bool:
        """Initialize the text agent with required tools."""
        if "TextAnalyzer" not in self.config.allowed_tools:
            return False
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text using the text analyzer tool.
        
        Args:
            input_data: Dictionary containing:
                - text: Text to analyze
                - analysis_type: Type of analysis to perform
                
        Returns:
            Dictionary containing analysis results
        """
        if not input_data.get("text"):
            raise ValidationError("Text is required")
            
        analysis_type = input_data.get("analysis_type", "word_count")
        
        # Use the text analyzer tool
        tool = self.tools.get("TextAnalyzer")
        if not tool:
            raise ValidationError("TextAnalyzer tool not available")
            
        result = await tool.execute({
            "text": input_data["text"],
            "analysis_type": analysis_type
        })
        
        return result.dict()
