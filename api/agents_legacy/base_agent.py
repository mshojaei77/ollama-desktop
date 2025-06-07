"""
Base Agent Module

This module defines the BaseAgent abstract class that all agents must implement.
It provides the foundation for creating new agents in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, AsyncGenerator, Callable


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.
    
    All agent implementations must inherit from this class and implement
    its abstract methods.
    """
    
    def __init__(self, agent_id: str, name: str, description: str, 
                 icon: str = "", tags: List[str] = None, 
                 config: Dict[str, Any] = None, 
                 example_prompts: List[str] = None,
                 tools: Optional[List[Any]] = None):
        """
        Initialize a new agent.
        
        Args:
            agent_id: Unique identifier for this agent
            name: Display name of the agent
            description: Description of what the agent does
            icon: URL or path to agent icon
            tags: List of tags/categories for this agent
            config: Configuration parameters for this agent
            example_prompts: List of example prompts to show in the UI
            tools: Optional list of tool definitions compatible with Ollama API
        """
        if not agent_id or not name:
            raise ValueError("agent_id and name are required.")
            
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.icon = icon
        self.tags = tags or []
        self.config = config or {}
        self.example_prompts = example_prompts or []
        self.tools = tools or []
        self.available_functions: Dict[str, Callable] = {}
        
    @abstractmethod
    async def process(self, message: str, session_id: str = None, 
                      context: Dict[str, Any] = None) -> str:
        """
        Process a message and return a response.
        
        Args:
            message: The user's message to process
            session_id: Optional session identifier for maintaining state
            context: Additional context information
            
        Returns:
            The agent's response as a string
        """
        pass
    
    @abstractmethod
    async def process_stream(self, message: str, session_id: str = None,
                           context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Process a message and stream the response.
        
        Args:
            message: The user's message to process
            session_id: Optional session identifier for maintaining state
            context: Additional context information
            
        Returns:
            An async generator yielding response chunks
        """
        raise NotImplementedError("Streaming not implemented for this agent.")
        yield
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get the agent's metadata.
        
        Returns:
            A dictionary containing the agent's metadata
        """
        return {
            "id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "tags": self.tags,
            "examplePrompts": self.example_prompts,
            "config": self.config,
            "tools": self.tools
        }
    
    def get_tools(self) -> List[Any]:
        """
        Return the list of tool definitions for this agent.
        """
        return self.tools

    def register_tool_function(self, name: str, func: Callable):
        """
        Register the implementation function for a tool.

        Args:
            name: The name of the tool function (must match the name in the tool definition).
            func: The callable function that implements the tool.
        """
        if not callable(func):
            raise ValueError(f"Provided item for tool '{name}' is not callable.")
        self.available_functions[name] = func
        print(f"Registered tool function: {name}")
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the agent with any necessary setup.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources used by the agent."""
        pass 