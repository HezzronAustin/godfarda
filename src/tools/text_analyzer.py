"""Example tool implementation for text analysis."""

from typing import Any, Dict
from .templates.tool_template import BaseTool, ToolResponse
from ..core.utils import ValidationError

class TextAnalyzer(BaseTool):
    """A tool for basic text analysis including word count and sentiment."""
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Define the parameter schema for the text analyzer.
        
        Returns:
            Dict containing parameter requirements
        """
        return {
            "text": str,
            "analysis_type": str,  # "word_count" or "sentiment"
        }
    
    async def execute(self, params: Dict[str, Any]) -> ToolResponse:
        """
        Execute text analysis based on the specified type.
        
        Args:
            params: Dictionary containing:
                - text: Text to analyze
                - analysis_type: Type of analysis to perform
                
        Returns:
            ToolResponse containing analysis results
        """
        try:
            # Validate parameters
            if not self.validate_params(params):
                raise ValidationError(
                    "Invalid parameters provided",
                    self.name
                )
            
            text = params["text"]
            analysis_type = params["analysis_type"]
            
            if analysis_type == "word_count":
                result = len(text.split())
            elif analysis_type == "sentiment":
                # Simple sentiment analysis (could be enhanced with proper NLP)
                positive_words = {"good", "great", "excellent", "happy", "positive"}
                negative_words = {"bad", "poor", "negative", "sad", "unhappy"}
                
                words = text.lower().split()
                positive_count = sum(1 for word in words if word in positive_words)
                negative_count = sum(1 for word in words if word in negative_words)
                
                if positive_count > negative_count:
                    result = "positive"
                elif negative_count > positive_count:
                    result = "negative"
                else:
                    result = "neutral"
            else:
                raise ValidationError(
                    f"Unknown analysis type: {analysis_type}",
                    self.name
                )
            
            return ToolResponse(
                success=True,
                data={
                    "analysis_type": analysis_type,
                    "result": result
                }
            )
            
        except Exception as e:
            return ToolResponse(
                success=False,
                error=str(e)
            )
