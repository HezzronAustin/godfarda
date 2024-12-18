from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import time
import json
import logging

from src.agents.base import BaseAgent
from src.agents.models import Agent, Tool, Function, AgentExecution

logger = logging.getLogger('agents.factory')

class DynamicAgent(BaseAgent):
    """Dynamically created agent from database definition"""
    
    def __init__(self, 
                 agent_def: Agent,
                 llm: Any,
                 session: Session,
                 max_depth: int = 3):
        logger.info(f"Initializing DynamicAgent: {agent_def.name}")
        super().__init__(agent_def.name, agent_def.description)
        self.agent_def = agent_def
        self.llm = llm
        self.session = session
        self.max_depth = max_depth
        
        try:
            self.tools = self._load_tools()
            self.functions = self._load_functions()
            logger.info(f"Loaded {len(self.tools)} tools and {len(self.functions)} functions for agent {self.name}")
            
            # Create the prompt template
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", agent_def.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
        except Exception as e:
            logger.error(f"Error initializing DynamicAgent {self.name}: {str(e)}")
            raise
        
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return a response"""
        logger.info(f"Processing message with agent {self.name}")
        start_time = time.time()
        
        try:
            # Create execution record
            execution = AgentExecution(
                agent_id=self.agent_def.id,
                input_data={'message': message},
                status='in_progress'
            )
            self.session.add(execution)
            self.session.commit()
            logger.debug(f"Created execution record for agent {self.name}")
            
            # Prepare chat history
            chat_history = []
            
            # Format the prompt
            prompt_value = self.prompt.format_messages(
                chat_history=chat_history,
                input=message
            )
            logger.debug(f"Formatted prompt for agent {self.name}")
            
            # Get response from LLM
            logger.debug(f"Sending prompt to LLM for agent {self.name}")
            response = await self.llm.agenerate([prompt_value])
            result = response.generations[0][0].text
            logger.debug(f"Received response from LLM for agent {self.name}")
            
            # Update execution record with success
            execution_time = time.time() - start_time
            execution.status = 'success'
            execution.output_data = {'response': result}
            execution.execution_time = execution_time
            execution.execution_metadata = {
                'prompt_tokens': len(str(prompt_value)),
                'completion_tokens': len(result),
                'total_tokens': len(str(prompt_value)) + len(result)
            }
            self.session.commit()
            
            logger.info(f"Successfully processed message with agent {self.name} in {execution_time:.2f}s")
            return {'response': result}
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error processing message with agent {self.name}: {str(e)}", exc_info=True)
            
            # Update execution record with error
            if 'execution' in locals():
                execution.status = 'failure'
                execution.error_message = str(e)
                execution.execution_time = execution_time
                execution.execution_metadata = {
                    'error_type': type(e).__name__,
                    'error_details': str(e)
                }
                self.session.commit()
            raise
            
    def _load_tools(self) -> List[Dict[str, Any]]:
        """Load tools associated with this agent"""
        logger.debug(f"Loading tools for agent {self.name}")
        tools = []
        for tool in self.agent_def.tools:
            try:
                tools.append({
                    'name': tool.name,
                    'description': tool.description,
                    'config': tool.config_data
                })
                logger.debug(f"Loaded tool {tool.name} for agent {self.name}")
            except Exception as e:
                logger.error(f"Error loading tool {tool.name} for agent {self.name}: {str(e)}")
                raise
        return tools
        
    def _load_functions(self) -> List[Dict[str, Any]]:
        """Load functions associated with this agent"""
        logger.debug(f"Loading functions for agent {self.name}")
        functions = []
        for function in self.agent_def.functions:
            try:
                functions.append({
                    'name': function.name,
                    'description': function.description,
                    'code': function.code,
                    'config': function.config_data
                })
                logger.debug(f"Loaded function {function.name} for agent {self.name}")
            except Exception as e:
                logger.error(f"Error loading function {function.name} for agent {self.name}: {str(e)}")
                raise
        return functions
