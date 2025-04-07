"""
Agent Registry Module

This module handles the discovery, registration, and management of agents.
It provides functions to list, get, and initialize agents.
"""

import os
import sys
import importlib
import inspect
import logging
import traceback
from typing import Dict, List, Type, Any, Optional

from .base_agent import BaseAgent

# Setup logging with more detailed format
logger = logging.getLogger("agent_registry")


class AgentRegistry:
    """
    Registry for managing all available agents in the system.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self._agents: Dict[str, BaseAgent] = {}
        self._initialized = False
        
    async def initialize(self):
        """
        Discover and initialize all agents in the agents directory.
        """
        if self._initialized:
            logger.info("Registry already initialized, skipping")
            return
            
        # Get the directory where agents are stored
        agents_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Looking for agents in: {agents_dir}")
        
        # List all files in directory for debugging
        all_files = os.listdir(agents_dir)
        logger.info(f"Files in agents directory: {all_files}")
        
        # Get a list of all Python files in the agents directory
        agent_files = [
            f[:-3] for f in os.listdir(agents_dir) 
            if f.endswith('.py') and 
            f != '__init__.py' and 
            f != 'base_agent.py' and
            f != 'registry.py' and
            f != 'routes.py'
        ]
        
        logger.info(f"Discovered agent files: {agent_files}")
        
        # Import each agent module and find agent classes
        for agent_file in agent_files:
            try:
                # Import the module - fix the module path to not include 'api'
                module_name = f"agents.{agent_file}"
                logger.info(f"Trying to import module: {module_name}")
                
                module = importlib.import_module(module_name)
                logger.info(f"Successfully imported module: {module_name}")
                
                # Find all classes in the module that inherit from BaseAgent
                agent_classes = []
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseAgent) and 
                        obj is not BaseAgent):
                        agent_classes.append((name, obj))
                
                logger.info(f"Found {len(agent_classes)} agent classes in {module_name}: {[name for name, _ in agent_classes]}")
                
                for name, obj in agent_classes:
                    try:
                        # Instantiate the agent
                        logger.info(f"Instantiating agent class: {name}")
                        agent = obj()
                        
                        # Initialize the agent
                        logger.info(f"Initializing agent: {name} ({agent.agent_id})")
                        success = await agent.initialize()
                        
                        if success:
                            # Register the agent
                            self._agents[agent.agent_id] = agent
                            logger.info(f"Successfully registered agent: {agent.name} ({agent.agent_id})")
                        else:
                            logger.warning(f"Failed to initialize agent: {agent.name} - initialize() returned False")
                    except Exception as e:
                        logger.error(f"Error instantiating or initializing agent class {name}: {str(e)}")
                        logger.error(traceback.format_exc())
                            
            except Exception as e:
                logger.error(f"Error loading agent module {agent_file}: {str(e)}")
                logger.error(traceback.format_exc())
                
        self._initialized = True
        logger.info(f"Agent registry initialized with {len(self._agents)} agents")
        if self._agents:
            logger.info(f"Registered agents: {[agent.name for agent in self._agents.values()]}")
        else:
            logger.warning("No agents were successfully registered")
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """
        Get a list of all registered agents' metadata.
        
        Returns:
            List of agent metadata dictionaries
        """
        return [agent.get_metadata() for agent in self._agents.values()]
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The unique identifier of the agent
            
        Returns:
            The agent instance or None if not found
        """
        return self._agents.get(agent_id)
    
    def get_agents_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """
        Get all agents with a specific tag.
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of agent metadata dictionaries
        """
        return [
            agent.get_metadata() for agent in self._agents.values()
            if tag in agent.tags
        ]
    
    async def cleanup(self):
        """Clean up all agent resources."""
        for agent in self._agents.values():
            try:
                await agent.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up agent {agent.name}: {str(e)}")
        
        self._agents = {}
        self._initialized = False


# Create a singleton instance of the registry
agent_registry = AgentRegistry() 