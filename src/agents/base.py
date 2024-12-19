from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.chat_models.ollama import ChatOllama
import json
import os

class LLMConfig:
    """Configuration for LLM settings"""
    def __init__(
        self,
        model_name: str = "llama3.2:3b",
        temperature: float = 0.6,
        top_p: float = 0.9,
        repeat_penalty: float = 1.1,
        context_window: int = 8192,
        timeout: int = 120,
        streaming: bool = False,
        max_iterations: int = 5,
        base_url: Optional[str] = None
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.context_window = context_window
        self.timeout = timeout
        self.streaming = streaming
        self.max_iterations = max_iterations
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL')

    def create_llm(self) -> ChatOllama:
        """Create a new LLM instance with the configured settings"""
        return ChatOllama(
            model=self.model_name,
            temperature=self.temperature,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            context_window=self.context_window,
            timeout=self.timeout,
            streaming=self.streaming,
            base_url=self.base_url
        )

class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(
        self,
        agent_def: Any,
        session: Session,
        description: str = None,
        agent_type: AgentType = AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        tools: List[Any] = None
    ):
        self.name = agent_def.name
        self.description = description
        self.agent_def = agent_def
        self.session = session
        self.llm_config = agent_def.config_data.get('llm', {})
        self.llm = self._create_llm()
        self.agent_type = agent_type
        self.tools = tools or []
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        if tools:
            self.agent_executor = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=agent_type,
                verbose=True,
                memory=self.memory,
                max_iterations=5
            )
        
    def _create_llm(self):
        """Create LLM instance from config"""
        from langchain_community.chat_models import ChatOllama
        
        config = self.llm_config.copy()
        model = config.pop('model', 'llama2')
        
        return ChatOllama(
            model=model,
            **{k: v for k, v in config.items() if v is not None}
        )
        
    @abstractmethod
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return a response"""
        pass
        
    async def can_handle(self, messages: List[BaseMessage], conversation_id: str) -> bool:
        """Check if this agent can handle the given messages
        
        Default implementation returns True if the agent's name is mentioned
        in the last message. Override this method for more sophisticated checks.
        """
        last_message = self._extract_last_message(messages)
        if not last_message:
            return False
            
        # Simple check - see if agent name is mentioned
        return self.name.lower() in last_message.lower()
        
    def _format_chat_history(self, messages: List[BaseMessage]) -> str:
        """Format chat history into a string"""
        formatted = []
        for msg in messages:
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            formatted.append(f"{role}: {msg.content}")
        return "\n".join(formatted)
        
    def _extract_last_message(self, messages: List[BaseMessage]) -> Optional[str]:
        """Extract the last message from chat history"""
        if not messages:
            return None
        return messages[-1].content
        
    def _format_response(self, response: Any) -> Dict[str, Any]:
        """Format the response into a standardized structure"""
        if isinstance(response, dict):
            return response
        if isinstance(response, str):
            return {"response": response}
        return {"response": str(response)}
        
    def create_chain(self, prompt_template: str, output_key: str = "text") -> LLMChain:
        """Create a new LLM chain with the configured LLM"""
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["input"]
        )
        return LLMChain(
            llm=self.llm,
            prompt=prompt,
            output_key=output_key
        )
