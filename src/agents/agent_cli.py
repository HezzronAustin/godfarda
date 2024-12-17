#!/usr/bin/env python3

import argparse
import importlib
import os
import sys
from typing import Any, Dict, List, Optional
import inspect
import asyncio
import json

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.base import AgentConfig
from src.core.registry import registry
from src.tools.ai.ollama.chat import OllamaChatTool
from src.core.utils import ToolException

# Register the Ollama chat tool
try:
    registry.register_tool(OllamaChatTool)
except ToolException:
    # Tool might already be registered, that's fine
    pass

def get_available_agents() -> List[str]:
    """Get a list of available agents in the agents directory."""
    agents_dir = os.path.dirname(os.path.abspath(__file__))
    agents = []
    
    for item in os.listdir(agents_dir):
        if os.path.isdir(os.path.join(agents_dir, item)) and not item.startswith('_') and not item in ['templates', 'tests', 'communications']:
            agents.append(item)
    
    return agents

def load_agent(agent_name: str) -> Any:
    """Dynamically load an agent module."""
    try:
        # Import the agent module
        module = importlib.import_module(f"agents.{agent_name}.{agent_name}_agent")
        
        # Find the agent class in the module
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and name.lower() == agent_name:
                return obj
        raise ValueError(f"No agent class found in {agent_name}_agent.py")
    except ImportError as e:
        print(f"Error loading agent '{agent_name}': {str(e)}")
        return None

async def interact_with_agent(agent_class: Any, message: str) -> None:
    """Interact with the specified agent."""
    try:
        # Create basic agent config
        config = AgentConfig(
            name=agent_class.__name__,
            description="CLI interaction",
            capabilities=[],
            tools=[]
        )
        
        # Initialize the agent
        agent = agent_class(config)
        init_success = await agent.initialize()
        
        if not init_success:
            print("Failed to initialize agent")
            return
        
        # Format message as expected by the agent
        input_data = {
            "message": message,  # Send message directly as string
            "user_info": {
                "id": "cli_user",
                "name": "CLI User",
                "username": "cli_user",
                "first_name": "CLI",
                "last_name": "User"
            },
            "platform": "cli"
        }
        
        # Process the message
        response = await agent.process(input_data)
        if isinstance(response, dict):
            if "error" in response:
                print(f"\nError: {response['error']}")
                if "response" in response:
                    print(f"Details: {response['response']}")
            else:
                print(f"\nAgent Response:\n{json.dumps(response, indent=2)}")
        else:
            print(f"\nAgent Response:\n{response}")
        
        # Cleanup
        await agent.cleanup()
        
    except Exception as e:
        print(f"Error interacting with agent: {str(e)}")

async def async_main():
    # Get available agents
    available_agents = get_available_agents()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Interact with AI agents')
    parser.add_argument('action', choices=['list', 'interact'], help='Action to perform')
    parser.add_argument('--agent', choices=available_agents, help='Name of the agent to interact with')
    parser.add_argument('--message', help='Message to send to the agent')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        print("\nAvailable Agents:")
        for agent in available_agents:
            print(f"- {agent}")
        return
        
    # For interact, we need both agent and message
    if args.action == 'interact':
        if not args.agent:
            print("Error: --agent is required for interact action")
            return
        if not args.message:
            print("Error: --message is required for interact action")
            return
            
        # Load and interact with the specified agent
        agent_class = load_agent(args.agent)
        if agent_class:
            await interact_with_agent(agent_class, args.message)

def main():
    asyncio.run(async_main())

if __name__ == '__main__':
    main()
