from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import time
import json

from src.agents.base import BaseAgent
from src.agents.models import Agent, Tool, Function, AgentExecution

class DynamicAgent(BaseAgent):
    """Dynamically created agent from database definition"""
    
    def __init__(self, 
                 agent_def: Agent,
                 llm: Any,
                 session: Session,
                 max_depth: int = 3):
        super().__init__(agent_def.name, agent_def.description)
        self.agent_def = agent_def
        self.llm = llm
        self.session = session
        self.max_depth = max_depth
        self.tools = self._load_tools()
        self.functions = self._load_functions()
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", agent_def.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return a response"""
        try:
            # Start timing
            start_time = time.time()
            
            # Create execution record
            execution = AgentExecution(
                agent_id=self.agent_def.id,
                input_data={'message': message},
                status='in_progress'
            )
            self.session.add(execution)
            self.session.commit()
            
            # Prepare chat history
            chat_history = []
            
            # Format the prompt
            prompt_value = self.prompt.format_messages(
                chat_history=chat_history,
                input=message
            )
            
            # Get response from LLM
            response = await self.llm.agenerate([prompt_value])
            result = response.generations[0][0].text
            
            # Update execution record with success
            execution.status = 'success'
            execution.output_data = {'response': result}
            execution.execution_time = time.time() - start_time
            execution.execution_metadata = {
                'prompt_tokens': len(str(prompt_value)),
                'completion_tokens': len(result),
                'total_tokens': len(str(prompt_value)) + len(result)
            }
            self.session.commit()
            
            return {'response': result}
            
        except Exception as e:
            # Update execution record with error
            execution.status = 'failure'
            execution.error_message = str(e)
            execution.execution_time = time.time() - start_time
            execution.execution_metadata = {
                'error_type': type(e).__name__,
                'error_details': str(e)
            }
            self.session.commit()
            raise
            
    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load tools associated with this agent"""
        tools = []
        for tool in self.agent_def.tools:
            tools.append({
                'name': tool.name,
                'description': tool.description,
                'config': tool.config_data
            })
        return tools
        
    def _load_functions(self) -> List[Dict[str, Any]]:
        """Load functions associated with this agent"""
        functions = []
        for function in self.agent_def.functions:
            functions.append({
                'name': function.name,
                'description': function.description,
                'code': function.code,
                'config': function.config_data
            })
        return functions
