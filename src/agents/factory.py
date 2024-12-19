from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import time
import json
import logging
import os

from src.agents.base import BaseAgent
from src.agents.models import Agent, Tool, AgentExecution
from src.agents.tool_manager import ToolManager
from langchain_community.chat_models import ChatOllama  # Assuming ChatOllama is imported from langchain.llms

logger = logging.getLogger('agents.factory')

class DynamicAgent(BaseAgent):
    """Dynamically created agent from database definition"""
    
    def __new__(cls, agent_def: Agent, session: Session, max_depth: int = 3):
        logger.info(f"Initializing DynamicAgent: {agent_def.name}")
        instance = super().__new__(cls)
        instance.name = agent_def.name
        instance.description = agent_def.description
        instance.agent_def = agent_def
        instance.session = session
        instance.max_depth = max_depth
        instance.tools = {}  # Will store loaded tool functions
        
        try:
            # Load tool implementations
            loaded_tools = ToolManager.load_tools(agent_def.tools)
            
            # Create wrapped tool functions with configurations
            for tool_name, loaded_func in loaded_tools.items():
                tool = next(t for t in agent_def.tools if t.name == tool_name)
                instance.tools[tool_name] = ToolManager.create_tool_function(loaded_func, tool)
                
            logger.info(f"Loaded {len(instance.tools)} tools for agent {instance.name}")
            
            # Create the prompt template
            instance.prompt = ChatPromptTemplate.from_messages([
                ("system", agent_def.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])
            
            return instance
            
        except Exception as e:
            logger.error(f"Error initializing DynamicAgent {agent_def.name}: {str(e)}")
            raise
    
    async def get_llm_response(self, prompt_value) -> str:
        """Get response from LLM with streaming support"""
        logger.debug(f"Sending prompt to LLM for agent {self.name}")
        response_text = ""
        
        try:
            if self.llm_config.get('streaming', False):
                async for chunk in self.llm.astream([prompt_value]):
                    response_text += chunk.content
            else:
                # Non-streaming mode
                response = await self.llm.agenerate([prompt_value])
                response_text = response.generations[0][0].text
            
            return response_text
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}", exc_info=True)
            raise
    
    async def process_message(self, message: str) -> Dict[str, Any]:
        """Process a message and return a response"""
        logger.info(f"Processing message with agent {self.name}")
        start_time = time.time()
        
        try:
            # Get a fresh copy of agent_def from the database
            agent_def = self.session.query(Agent).get(self.agent_def.id)
            if not agent_def:
                raise ValueError(f"Agent {self.name} not found in database")
            
            # Create execution record
            execution = AgentExecution(
                agent_id=agent_def.id,
                input_data={'message': message},
                status='in_progress'
            )
            self.session.add(execution)
            self.session.commit()
            logger.debug(f"Created execution record for agent {self.name}")
            
            # Format the prompt
            prompt_value = self.prompt.format_messages(
                chat_history=[],  # Chat history handled by parent
                input=message
            )
            logger.debug(f"Formatted prompt for agent {self.name}")
            
            # Get response from LLM
            response_text = await self.get_llm_response(prompt_value)
            
            # Parse response if JSON format is required
            requires_json = (
                agent_def.config_data.get('output', {}).get('format') == 'json' or 
                agent_def.config_data.get("requires_structured_output", False)
            )
            
            if requires_json:
                try:
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON response for agent {self.name}")
                    result = {"response": response_text}
            else:
                result = {"response": response_text}
            
            # Update execution record with success
            execution_time = time.time() - start_time
            execution.status = 'success'
            execution.output_data = result
            execution.execution_time = execution_time
            
            # Get token counts if method available
            if hasattr(self.llm, 'get_num_tokens'):
                token_metrics = {
                    'prompt_tokens': self.llm.get_num_tokens(str(prompt_value)),
                    'completion_tokens': self.llm.get_num_tokens(response_text),
                    'total_tokens': self.llm.get_num_tokens(str(prompt_value)) + self.llm.get_num_tokens(response_text)
                }
            else:
                token_metrics = {
                    'prompt_chars': len(str(prompt_value)),
                    'completion_chars': len(response_text),
                    'total_chars': len(str(prompt_value)) + len(response_text)
                }
            
            execution.execution_data = {
                **token_metrics,
                'tool_usage': [t.name for t in agent_def.tools if t.name in self.tools],
                'llm_config': agent_def.config_data.get('llm', {})
            }
            self.session.commit()
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error processing message with agent {self.name}: {str(e)}", exc_info=True)
            
            if 'execution' in locals():
                execution.status = 'failure'
                execution.error_message = str(e)
                execution.execution_time = execution_time
                execution.execution_data = {
                    'error_type': type(e).__name__,
                    'error_details': str(e),
                    'tool_usage': [],  # Can't access agent_def here
                    'llm_config': {}
                }
                self.session.commit()
            
            raise