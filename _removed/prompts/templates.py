from langchain.prompts import PromptTemplate
from typing import List, Dict, Any
from datetime import datetime

# Base template for RAG responses
RAG_TEMPLATE = """You are a helpful AI assistant with access to relevant information about the user and conversation history.

{context}

Previous conversation:
{conversation_history}

Current question: {query}

Instructions:
1. Use the provided user information and context to give a personalized response
2. Reference the user by their name or username when appropriate
3. Maintain conversation continuity by acknowledging previous interactions when relevant
4. If referring to previous conversations, be specific about which part you're referencing
5. If the information is not in the context, acknowledge that and provide general guidance
6. Keep responses clear and concise while maintaining context
7. Maintain a helpful and professional tone

Response:"""

# Template for system analysis/technical questions
TECHNICAL_TEMPLATE = """You are a technical expert analyzing the following information:

Context from documentation and code:
{context}

Previous discussion:
{conversation_history}

Technical question: {query}

Please provide:
1. A clear technical explanation
2. Any relevant code examples or references
3. Best practices or considerations
4. Potential issues to be aware of

Technical analysis:"""

# Template for summarization tasks
SUMMARY_TEMPLATE = """You are tasked with summarizing the following information:

Content to summarize:
{context}

Previous summaries and discussion:
{conversation_history}

Focus areas: {query}

Please provide:
1. A concise summary of key points
2. Important highlights or findings
3. Any relevant connections or patterns
4. Areas that need further clarification

Summary:"""

# Template for brainstorming and ideation
BRAINSTORM_TEMPLATE = """You are a creative problem-solver helping with ideation:

Relevant background:
{context}

Previous ideas and discussion:
{conversation_history}

Current challenge: {query}

Please provide:
1. Multiple creative approaches or solutions
2. Pros and cons of each approach
3. Building on any previous ideas
4. Practical next steps

Ideas and recommendations:"""

class PromptTemplates:
    def __init__(self):
        """Initialize prompt templates."""
        self.templates = {
            'default': PromptTemplate(
                template=RAG_TEMPLATE,
                input_variables=["context", "conversation_history", "query"]
            ),
            'technical': PromptTemplate(
                template=TECHNICAL_TEMPLATE,
                input_variables=["context", "conversation_history", "query"]
            ),
            'summary': PromptTemplate(
                template=SUMMARY_TEMPLATE,
                input_variables=["context", "conversation_history", "query"]
            ),
            'brainstorm': PromptTemplate(
                template=BRAINSTORM_TEMPLATE,
                input_variables=["context", "conversation_history", "query"]
            )
        }
    
    def get_template(self, template_type: str = 'default') -> PromptTemplate:
        """Get a specific prompt template."""
        return self.templates.get(template_type, self.templates['default'])
    
    def format_prompt(self, 
                     template_type: str,
                     context: str,
                     conversation_history: str,
                     query: str) -> str:
        """Format a prompt using the specified template."""
        template = self.get_template(template_type)
        return template.format(
            context=context,
            conversation_history=conversation_history,
            query=query
        )
