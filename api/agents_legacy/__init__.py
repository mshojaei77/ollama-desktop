"""
Agents Package

This package contains the agent system for the Ollama Desktop application.
Agents are specialized AI assistants with specific capabilities or knowledge.

To create a new agent:
1. Create a new Python file in this directory
2. Define a class that inherits from BaseAgent
3. Implement all the abstract methods
4. The agent will be automatically discovered and registered
"""

import logging

# Configure logging for agents
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

from .base_agent import BaseAgent
from .registry import agent_registry

__all__ = ["BaseAgent", "agent_registry"] 