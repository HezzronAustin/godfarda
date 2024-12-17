"""
Godfarda Agent - The top-level orchestrator agent.

This agent is responsible for:
1. Managing and coordinating all other agents
2. Understanding each agent's capabilities and tools
3. Routing requests to appropriate agents
4. Handling default communication when no specific agent is specified
"""

from typing import Dict, List, Any
import logging
import os
import importlib.util
from pathlib import Path
from src.agents.base import BaseAgent, AgentConfig
from .memory.memory_store import GodFardaMemory
import datetime
import json

logger = logging.getLogger(__name__)

class AgentInfo:
    """Information about an agent and its capabilities"""
    def __init__(self, name: str, description: str, capabilities: List[str], tools: List[str]):
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.tools = tools

class GodFarda(BaseAgent):
    """The top-level orchestrator agent that manages all other agents"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.agents: Dict[str, AgentInfo] = {}
        self.memory = GodFardaMemory()
        self.register_default_agents()
        
    def register_default_agents(self):
        """Register all available agents from the agents directory"""
        agents_dir = Path(__file__).parent.parent  # Get the agents directory
        
        # Iterate through all Python files in the agents directory
        for item in agents_dir.glob("**/*.py"):
            # Skip __init__.py, test files, and files in the godfarda directory
            if (item.name == "__init__.py" or 
                "test" in item.name.lower() or 
                "godfarda" in str(item) or
                "_template" in str(item) or
                item.parent.name == "__pycache__"):
                continue
                
            try:
                # Get the module name from the file path
                module_name = str(item.relative_to(agents_dir.parent)).replace("/", ".").replace(".py", "")
                
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, str(item))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for agent classes that inherit from BaseAgent
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            issubclass(attr, BaseAgent) and 
                            attr != BaseAgent):
                            
                            # Create an instance and get its capabilities
                            agent_name = attr_name.lower()
                            agent_info = AgentInfo(
                                name=agent_name,
                                description=attr.__doc__ or f"Agent {agent_name}",
                                capabilities=getattr(attr, "capabilities", []),
                                tools=getattr(attr, "tools", [])
                            )
                            
                            self.register_agent(agent_name, agent_info)
                            logger.info(f"Registered agent: {agent_name}")
                            
            except Exception as e:
                logger.error(f"Error loading agent from {item}: {str(e)}")
        
    def register_agent(self, name: str, agent_info: AgentInfo):
        """Register a new agent with its capabilities"""
        self.agents[name] = agent_info
        logger.info(f"Registered agent: {name} with capabilities: {agent_info.capabilities}")
        
    async def initialize(self) -> bool:
        """Initialize the Godfarda agent and its memory system"""
        try:
            # Log initialization
            logger.info(f"Initializing GodFarda with {len(self.agents)} registered agents")
            
            # Store initialization in memory
            self.memory.add_memory(
                "GodFarda initialization",
                "system",
                {"event": "initialization"},
                importance=1.0
            )
            
            # Initialize Ollama for AI responses
            from src.core.registry import registry
            
            ollama_class = registry.get_tool("OllamaChatTool")
            if not ollama_class:
                logger.error("OllamaChatTool not found in registry")
                return False
                
            self.ollama = ollama_class()
            if not await self.ollama.initialize():
                logger.error("Failed to initialize Ollama chat tool")
                return False
                
            logger.info("Ollama chat tool initialized successfully")
            
            logger.info("Godfarda agent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Godfarda: {str(e)}", exc_info=True)
            return False
            
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages with memory context"""
        try:
            message = input_data.get("message", "")
            user_info = input_data.get("user_info", {})
            platform = input_data.get("platform", "unknown")
            
            logger.info(f"GodFarda processing message: {message}")
            logger.info(f"From user: {json.dumps(user_info, indent=2)}")
            logger.info(f"Platform: {platform}")
            
            # Store message in memory
            self.memory.add_memory(
                f"User message: {message}",
                "conversation",
                {
                    "user": user_info,
                    "platform": platform,
                    "type": "incoming"
                }
            )
            
            # Get relevant memories for context
            relevant_memories = await self.memory.get_relevant_memories(message)
            memory_context = self._format_memories(relevant_memories)
            logger.info(f"Retrieved {len(relevant_memories)} relevant memories")
            
            # Update working memory with current context
            self.memory.update_working_memory("current_user", user_info)
            self.memory.update_working_memory("platform", platform)
            
            # If message starts with @, route to specific agent
            if message.startswith("@"):
                space_index = message.find(" ")
                if space_index == -1:
                    return {"error": "No message provided for agent"}
                    
                agent_name = message[1:space_index].lower()
                if agent_name not in self.agents:
                    available_agents = ", ".join([f"@{name}" for name in self.agents.keys()])
                    return {
                        "error": f"Unknown agent: {agent_name}",
                        "response": f"I don't know that agent. Available agents are: {available_agents}"
                    }
                    
                actual_message = message[space_index + 1:]
                return await self.delegate_to_agent(agent_name, actual_message, user_info, memory_context)
                
            # No specific agent mentioned, handle as Godfarda
            return await self.handle_as_godfarda(message, user_info, memory_context)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {"error": f"Failed to process message: {str(e)}"}
            
    def _format_memories(self, memories: List[Any]) -> str:
        """Format memories into a context string"""
        if not memories:
            return "No relevant previous context."
            
        formatted = ["Previous relevant context:"]
        for memory in memories:
            dt = datetime.datetime.fromtimestamp(memory.timestamp)
            timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            formatted.append(f"[{timestamp}] {memory.content}")
            
        return "\n".join(formatted)
            
    async def handle_as_godfarda(self, message: str, user_info: Dict[str, Any], memory_context: str) -> Dict[str, Any]:
        """Handle messages as Godfarda with memory context"""
        system_message = f"""You are Godfarda, the top-level AI orchestrator. You:
1. Know about all available agents and their capabilities
2. Can delegate tasks to specific agents when needed
3. Can handle general queries directly
4. Always maintain a helpful and knowledgeable demeanor



Available Agents:
{self._format_agent_info()}

Current User:
- Username: {user_info.get('username', 'unknown')}
- Name: {user_info.get('first_name', '')} {user_info.get('last_name', '')}

{memory_context}

Remember to:
1. Suggest specific agents when their expertise would be helpful
2. Question unclear instructions rather than assuming intent
3. Highlight potential trade-offs and risks for complex solutions
4. Never delete code or comments unless explicitly requested
5. Only make changes related to the task at hand"""

        try:
            response = await self.ollama.execute({
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ]
            })
            
            if not response.success:
                return {"error": f"Failed to get AI response: {response.error}"}
                
            response_content = response.data["message"]["content"]
            
            # Store response in memory
            self.memory.add_memory(
                f"Godfarda response: {response_content}",
                "conversation",
                {
                    "user": user_info,
                    "type": "outgoing"
                }
            )
            
            return {
                "response": response_content,
                "agent": "godfarda"
            }
            
        except Exception as e:
            logger.error(f"Error in Godfarda response: {str(e)}")
            return {"error": f"Failed to generate response: {str(e)}"}
            
    async def delegate_to_agent(self, agent_name: str, message: str, user_info: Dict[str, Any], memory_context: str) -> Dict[str, Any]:
        """Delegate a message to a specific agent with memory context"""
        agent_info = self.agents[agent_name]
        
        system_message = f"""You are {agent_name}, an AI assistant with expertise in {', '.join(agent_info.capabilities)}.
You have access to the following tools: {', '.join(agent_info.tools)}.
Respond according to your specific role and expertise.

Current User:
- Username: {user_info.get('username', 'unknown')}
- Name: {user_info.get('first_name', '')} {user_info.get('last_name', '')}

{memory_context}"""

        try:
            response = await self.ollama.execute({
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ]
            })
            
            if not response.success:
                return {"error": f"Failed to get agent response: {response.error}"}
                
            response_content = response.data["message"]["content"]
            
            # Store response in memory
            self.memory.add_memory(
                f"Agent {agent_name} response: {response_content}",
                "conversation",
                {
                    "user": user_info,
                    "agent": agent_name,
                    "type": "outgoing"
                }
            )
            
            return {
                "response": response_content,
                "agent": agent_name
            }
            
        except Exception as e:
            logger.error(f"Error in agent response: {str(e)}")
            return {"error": f"Failed to generate response: {str(e)}"}
            
    def _format_agent_info(self) -> str:
        """Format agent information for system message"""
        agent_info = []
        for name, info in self.agents.items():
            capabilities = ", ".join(info.capabilities)
            agent_info.append(f"@{name}: {info.description} (Capabilities: {capabilities})")
        return "\n".join(agent_info)

    def cleanup(self):
        """Clean up resources used by the agent."""
        # Clean up memory
        if self.memory:
            self.memory.clear_memories()
        
        # Clear agent registry
        self.agents.clear()
