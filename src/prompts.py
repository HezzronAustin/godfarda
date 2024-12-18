from typing import Dict, Any
from langchain.prompts import PromptTemplate

class PromptTemplates:
    def __init__(self):
        self.conversation_prompt = PromptTemplate(
            input_variables=["context", "conversation_history", "query"],
            template="""Context information and conversation history is below.
---------------------
{context}

{conversation_history}
---------------------
You are an AI assistant talking to a Telegram user. Please respond in a conversational, first-person manner as if directly speaking to the user.
Given the context information, conversation history, and no other information, answer the following question: {query}
If the available information doesn't provide enough context to answer fully, acknowledge what is known and indicate what additional information would be needed."""
        )

        self.context_prompt = PromptTemplate(
            input_variables=["document_type", "content"],
            template="""Source ({document_type}):
{content}"""
        )

        self.system_prompt = PromptTemplate(
            input_variables=[],
            template="""You are a helpful AI assistant that provides accurate, informative responses based on the given context.
You should:
1. Use the provided context to answer questions
2. Maintain a conversational, friendly tone
3. Acknowledge when information is incomplete
4. Stay focused on the user's query
5. Provide clear, structured responses"""
        )

        self.follow_up_prompt = PromptTemplate(
            input_variables=["previous_response", "query"],
            template="""Based on my previous response:
{previous_response}

How can I help you with your follow-up question: {query}"""
        )

    def format_conversation_prompt(self, context: str, conversation_history: str, query: str) -> str:
        """Format the main conversation prompt with the given inputs."""
        return self.conversation_prompt.format(
            context=context,
            conversation_history=conversation_history,
            query=query
        )

    def format_context(self, document_type: str, content: str) -> str:
        """Format a single context document."""
        return self.context_prompt.format(
            document_type=document_type,
            content=content
        )

    def get_system_prompt(self) -> str:
        """Get the system prompt."""
        return self.system_prompt.format()

    def format_follow_up(self, previous_response: str, query: str) -> str:
        """Format a follow-up question prompt."""
        return self.follow_up_prompt.format(
            previous_response=previous_response,
            query=query
        )
