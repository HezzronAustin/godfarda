from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import time
import json
import logging

from src.agents.base import BaseAgent
from src.agents.models import Agent, Tool, AgentExecution

logger = logging.getLogger('agents.factory')

class DynamicAgent(BaseAgent):
    """Dynamically created agent from database definition"""
    def __new__(self,
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
            logger.info(f"Loaded {len(self.tools)} tools for agent {self.name}")
            
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
            
            # Get response from LLM with streaming if supported
            logger.debug(f"Sending prompt to LLM for agent {self.name}")
            response_text = ""
            
            if hasattr(self.llm, 'astream'):
                async for chunk in self.llm.astream([prompt_value]):
                    response_text += chunk.content
            else:
                # Fallback for non-streaming LLMs
                response = await self.llm.agenerate([prompt_value])
                response_text = response.generations[0][0].text
                
            # Parse response if JSON format is required
            requires_json = (
                self.agent_def.llm_config.get('format') == 'json' or 
                self.agent_def.config_data.get("requires_structured_output")
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
                # Fallback metrics based on string length
                token_metrics = {
                    'prompt_chars': len(str(prompt_value)),
                    'completion_chars': len(response_text),
                    'total_chars': len(str(prompt_value)) + len(response_text)
                }
                
            execution.execution_metadata = {
                **token_metrics,
                'llm_provider': self.agent_def.llm_provider,
                'llm_model': self.agent_def.llm_model
            }
            self.session.commit()
            
            logger.info(f"Successfully processed message with agent {self.name} in {execution_time:.2f}s")
            return result
            
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
                    'error_details': str(e),
                    'llm_provider': self.agent_def.llm_provider,
                    'llm_model': self.agent_def.llm_model
                }
                self.session.commit()
            
            raise
            
    def _load_tools(self) -> Dict[str, Tool]:
        """Load tools for this agent"""
        return {tool.name: tool for tool in self.agent_def.tools}
