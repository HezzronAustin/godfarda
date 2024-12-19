from typing import Dict, Any, Optional, ClassVar
from sqlalchemy.orm import Session
from telethon import events, Button
from src.agents.models import Agent, Tool
from src.telegram.base import BaseTelegramHandler
import logging
import json

logger = logging.getLogger('telegram.agent_manager')

class AgentManager(BaseTelegramHandler):
    """Handler for managing agents through Telegram"""
    
    # Class variable to track user workflows across instances
    _user_workflows: ClassVar[Dict[int, Dict[str, Any]]] = {}
    
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        
    @classmethod
    def is_user_in_workflow(cls, user_id: int) -> bool:
        """Check if a user is currently in a workflow"""
        return user_id in cls._user_workflows
        
    async def register_handlers(self, client):
        """Register all agent management handlers"""
        client.add_event_handler(
            self.handle_create_agent,
            events.NewMessage(pattern='/create_agent')
        )
        client.add_event_handler(
            self.handle_list_agents,
            events.NewMessage(pattern='/list_agents')
        )
        client.add_event_handler(
            self.handle_agent_info,
            events.NewMessage(pattern='/agent_info')
        )
        client.add_event_handler(
            self.handle_workflow_message,
            events.NewMessage(func=self._is_workflow_message)
        )
        
    def _is_workflow_message(self, event) -> bool:
        """Check if this message is part of a workflow"""
        return (
            event.sender_id in self._user_workflows and
            not event.message.text.startswith('/')  # Not a command
        )
        
    async def handle_workflow_message(self, event):
        """Handle messages that are part of a workflow"""
        user_id = event.sender_id
        workflow = self._user_workflows.get(user_id)
        
        if not workflow:
            return
            
        if event.text.lower() == 'cancel':
            del self._user_workflows[user_id]
            await event.respond("❌ Agent creation cancelled.")
            return
            
        try:
            await self._process_workflow_step(event, workflow)
        except Exception as e:
            logger.error(f"Error in workflow: {str(e)}")
            del self._user_workflows[user_id]
            await event.respond(f"❌ Error creating agent: {str(e)}\nPlease try again.")
            
    async def _process_workflow_step(self, event, workflow):
        """Process a single step in the workflow"""
        step = workflow['step']
        user_id = event.sender_id
        
        if step == 'name':
            # Validate name
            name = event.text.strip()
            if not name or len(name) < 3:
                await event.respond("Name must be at least 3 characters long. Please try again:")
                return
                
            # Check if name already exists
            existing = self.session.query(Agent).filter(Agent.name == name).first()
            if existing:
                await event.respond("An agent with this name already exists. Please choose another name:")
                return
                
            workflow['data']['name'] = name
            workflow['step'] = 'description'
            await event.respond("Great! Now enter a description for the agent:")
            
        elif step == 'description':
            workflow['data']['description'] = event.text
            workflow['step'] = 'system_prompt'
            await event.respond(
                "Please enter the system prompt for the agent.\n"
                "This is the initial instruction that defines the agent's behavior:"
            )
            
        elif step == 'system_prompt':
            workflow['data']['system_prompt'] = event.text
            workflow['step'] = 'llm_config'
            
            # Ask for LLM configuration with a more user-friendly format
            await event.respond(
                "Now let's configure the LLM settings. Please provide the configuration in this format:\n\n"
                "provider: ollama\n"
                "model: mistral\n"
                "temperature: 0.7\n"
                "top_p: 1.0\n\n"
                "You can copy and modify the above template."
            )
            
        elif step == 'llm_config':
            try:
                # Parse YAML-like format to JSON
                config_text = event.text
                config_dict = {}
                
                for line in config_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        # Convert string numbers to float/int
                        try:
                            if '.' in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            pass
                        config_dict[key] = value
                
                workflow['data']['llm_provider'] = config_dict.get('provider', 'ollama')
                workflow['data']['llm_model'] = config_dict.get('model', 'mistral')
                workflow['data']['llm_config'] = config_dict
                
                # Create the agent
                new_agent = Agent(
                    name=workflow['data']['name'],
                    description=workflow['data']['description'],
                    system_prompt=workflow['data']['system_prompt'],
                    llm_provider=workflow['data']['llm_provider'],
                    llm_model=workflow['data']['llm_model'],
                    llm_config=workflow['data']['llm_config']
                )
                
                self.session.add(new_agent)
                self.session.commit()
                
                # Cleanup workflow
                del self._user_workflows[user_id]
                
                await event.respond(
                    f"✅ Agent '{new_agent.name}' created successfully!\n\n"
                    f"Description: {new_agent.description}\n"
                    f"LLM Provider: {new_agent.llm_provider}\n"
                    f"Model: {new_agent.llm_model}"
                )
                
            except Exception as e:
                await event.respond(
                    "❌ Invalid configuration format. Please try again using the template provided:\n\n"
                    "provider: ollama\n"
                    "model: mistral\n"
                    "temperature: 0.7\n"
                    "top_p: 1.0"
                )
        
    async def handle_create_agent(self, event):
        """Start the agent creation process"""
        user_id = event.sender_id
        
        # Initialize workflow state
        self._user_workflows[user_id] = {
            'step': 'name',
            'data': {}
        }
        
        keyboard = [[Button.text("Cancel")]]
        
        await event.respond(
            "Let's create a new agent! Please enter the agent's name:",
            buttons=keyboard
        )
        
    async def handle_list_agents(self, event):
        """List all available agents"""
        agents = self.session.query(Agent).all()
        
        if not agents:
            await event.respond("No agents found.")
            return
            
        response = "Available Agents:\n\n"
        for agent in agents:
            response += f"📱 {agent.name}\n"
            response += f"Description: {agent.description}\n"
            response += f"Model: {agent.llm_provider}/{agent.llm_model}\n\n"
            
        await event.respond(response)
        
    async def handle_agent_info(self, event):
        """Show detailed information about an agent"""
        # Extract agent name from command
        try:
            agent_name = event.text.split(' ', 1)[1]
        except IndexError:
            await event.respond(
                "Please specify an agent name.\n"
                "Usage: /agent_info <agent_name>"
            )
            return
            
        agent = self.session.query(Agent).filter(Agent.name == agent_name).first()
        
        if not agent:
            await event.respond(f"Agent '{agent_name}' not found.")
            return
            
        response = f"📱 Agent: {agent.name}\n\n"
        response += f"Description: {agent.description}\n"
        response += f"LLM Provider: {agent.llm_provider}\n"
        response += f"Model: {agent.llm_model}\n"
        response += f"Temperature: {agent.llm_config.get('temperature', 'N/A')}\n"
        response += f"Top P: {agent.llm_config.get('top_p', 'N/A')}\n"
        response += "\nSystem Prompt:\n"
        response += f"{agent.system_prompt}\n"
        
        # Add tool information if available
        if agent.tools:
            response += "\nTools:\n"
            for tool in agent.tools:
                response += f"- {tool.name}\n"
                
        await event.respond(response)
