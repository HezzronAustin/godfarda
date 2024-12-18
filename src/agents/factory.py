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
    
    def _load_tools(self) -> Dict[str, Any]:
        """Load tool implementations from database definitions"""
        tools = {}
        for tool in self.agent_def.tools:
            try:
                # Import the module containing the function
                module_path, func_name = tool.function_name.rsplit('.', 1)
                module = importlib.import_module(module_path)
                tools[tool.name] = getattr(module, func_name)
            except Exception as e:
                print(f"Failed to load tool {tool.name}: {e}")
        return tools
    
    def _load_functions(self) -> Dict[str, Any]:
        """Load function implementations from database definitions"""
        functions = {}
        for func in self.agent_def.functions:
            try:
                # Create function from stored Python code
                exec(func.python_code)
                functions[func.name] = locals()[func.name]
            except Exception as e:
                print(f"Failed to load function {func.name}: {e}")
        return functions
    
    async def can_handle(self, 
                        messages: List[BaseMessage], 
                        conversation_id: str,
                        chain_depth: int = 0) -> bool:
        """Check if agent can handle the messages based on input schema"""
        if chain_depth >= self.max_depth:
            return False
            
        if not messages:
            return False
            
        latest_message = messages[-1].content
        
        # Use LLM to check if message matches input schema
        schema_check = await self.llm.apredict_messages([
            SystemMessage(content=f"""Determine if the following message matches this JSON schema:
            {self.agent_def.input_schema}
            
            Respond with only 'yes' or 'no'."""),
            HumanMessage(content=latest_message)
        ])
        
        return schema_check.content.strip().lower() == 'yes'
    
    async def process(self,
                     messages: List[BaseMessage],
                     conversation_id: str,
                     chain_depth: int = 0,
                     parent_execution_id: Optional[int] = None,
                     **kwargs) -> str:
        """Process messages using available tools and functions"""
        start_time = time.time()
        
        # Create execution record
        execution = AgentExecution(
            agent_id=self.agent_def.id,
            conversation_id=conversation_id,
            input_data={'messages': [m.content for m in messages]},
            chain_depth=chain_depth,
            parent_execution_id=parent_execution_id,
            status='in_progress'
        )
        self.session.add(execution)
        self.session.commit()
        
        try:
            # Format messages for the prompt
            chat_history = messages[:-1]
            latest_message = messages[-1].content
            
            # Get available functions for the LLM
            openai_functions = [
                convert_to_openai_function(func)
                for func in list(self.tools.values()) + list(self.functions.values())
            ]
            
            # Get the model's response
            response = await self.llm.apredict_messages(
                messages=self.prompt.format_messages(
                    input=latest_message,
                    chat_history=chat_history
                ),
                functions=openai_functions,
                temperature=self.agent_def.temperature,
                top_p=self.agent_def.top_p,
                presence_penalty=self.agent_def.presence_penalty,
                frequency_penalty=self.agent_def.frequency_penalty
            )
            
            # Handle function calling
            if response.additional_kwargs.get("function_call"):
                func_call = response.additional_kwargs["function_call"]
                func_name = func_call["name"]
                func_args = eval(func_call["arguments"])
                
                # Find and execute the function
                func = self.tools.get(func_name) or self.functions.get(func_name)
                if func:
                    if inspect.iscoroutinefunction(func):
                        result = await func(**func_args)
                    else:
                        result = func(**func_args)
                        
                    # Get final response incorporating function result
                    final_response = await self.llm.apredict_messages(
                        messages=[
                            *self.prompt.format_messages(
                                input=latest_message,
                                chat_history=chat_history
                            ),
                            response,
                            SystemMessage(content=f"Function {func_name} returned: {result}")
                        ]
                    )
                    response_text = final_response.content
                else:
                    response_text = f"Error: Function {func_name} not found"
            else:
                response_text = response.content
            
            # Check if response meets output schema
            schema_check = await self.llm.apredict_messages([
                SystemMessage(content=f"""Determine if the following response matches this JSON schema:
                {self.agent_def.output_schema}
                
                Respond with only 'yes' or 'no'."""),
                HumanMessage(content=response_text)
            ])
            
            # If response doesn't match schema and we have a fallback agent
            if (schema_check.content.strip().lower() == 'no' and 
                self.agent_def.fallback_agent_id and 
                chain_depth < self.max_depth):
                
                # Get fallback agent
                fallback_agent = self.session.query(Agent).get(self.agent_def.fallback_agent_id)
                if fallback_agent:
                    # Create new dynamic agent instance
                    fallback = DynamicAgent(
                        fallback_agent,
                        self.llm,
                        self.session,
                        self.max_depth
                    )
                    
                    # Try processing with fallback agent
                    response_text = await fallback.process(
                        messages,
                        conversation_id,
                        chain_depth + 1,
                        execution.id
                    )
            
            # Update execution record
            execution.status = 'success'
            execution.output_data = {'response': response_text}
            execution.execution_time = time.time() - start_time
            self.session.commit()
            
            return response_text
            
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
