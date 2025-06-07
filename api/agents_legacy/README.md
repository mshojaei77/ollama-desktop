# Ollama Desktop Agents System

The Agents system provides a flexible way to extend Ollama Desktop with specialized AI assistants, each with their own capabilities and knowledge domains.

## Overview

Agents are specialized AI assistants that can be easily created and added to the system. Each agent is defined in its own Python file in the `api/agents/` directory and is automatically discovered and registered when the application starts.

## Creating a New Agent

To create a new agent:

1. Create a new Python file in the `api/agents/` directory (e.g., `my_new_agent.py`)
2. Define a class that inherits from `BaseAgent` and implements all its abstract methods
3. The agent will be automatically discovered and registered on application startup

### Example Agent Template

```python
"""
My New Agent

Brief description of what this agent does.
"""

import logging
from typing import Dict, List, Any, AsyncGenerator, Optional

from .base_agent import BaseAgent
from api.ollama_client import OllamaPackage


logger = logging.getLogger("my_new_agent")


class MyNewAgent(BaseAgent):
    """
    Description of your agent's purpose and capabilities.
    """
    
    def __init__(self):
        """Initialize the agent."""
        super().__init__(
            agent_id="my-new-agent",  # Unique ID for this agent
            name="My New Agent",      # Display name
            description="Description of what this agent does.",
            icon="https://example.com/icon.png",  # URL to agent's icon
            tags=["tag1", "tag2"],    # Categories for this agent
            config={
                "default_model": "llama3.2",
                "system_message": """Specific system message for this agent."""
            }
        )
        self.chatbot = None
        
    async def initialize(self) -> bool:
        """Initialize the agent and set up required resources."""
        try:
            # Initialize the Ollama chatbot or other resources
            self.chatbot = await OllamaPackage.create_standalone_chatbot(
                model_name=self.config["default_model"],
                system_message=self.config["system_message"]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            return False
    
    async def process(self, message: str, session_id: str = None, 
                     context: Dict[str, Any] = None) -> str:
        """Process a message and return a response."""
        if not self.chatbot:
            return "Sorry, I'm not initialized properly. Please try again later."
        
        try:
            # Process the message - add your custom logic here
            response = await self.chatbot.chat(message)
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I encountered an error processing your request."
    
    async def process_stream(self, message: str, session_id: str = None,
                           context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Process a message and stream the response."""
        if not self.chatbot:
            yield "Sorry, I'm not initialized properly. Please try again later."
            return
        
        try:
            # Stream the response - add your custom logic here
            async for chunk in self.chatbot.chat_stream(message):
                if chunk is not None:
                    yield chunk
        except Exception as e:
            logger.error(f"Error streaming response: {str(e)}")
            yield "I encountered an error processing your request."
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        if self.chatbot:
            try:
                await self.chatbot.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up resources: {str(e)}")
            finally:
                self.chatbot = None
```

## Agent Implementation Tips

1. **Unique ID**: Each agent must have a unique `agent_id`.
2. **Error Handling**: Always include error handling in your agent methods to prevent crashes.
3. **Resource Management**: Initialize resources in `initialize()` and clean them up in `cleanup()`.
4. **Session Tracking**: Use the `session_id` parameter to maintain state between user interactions.
5. **Streaming**: Implement both `process()` for single responses and `process_stream()` for streaming responses.
6. **Tags**: Use tags to categorize your agent so users can find it more easily.

## Accessing Agents from the API

Agents can be accessed via the following API endpoints:

- `GET /agents` - List all available agents
- `GET /agents/{agent_id}` - Get information about a specific agent
- `GET /agents/tag/{tag}` - Get all agents with a specific tag
- `POST /agents/{agent_id}/message` - Send a message to an agent
- `POST /agents/{agent_id}/message/stream` - Send a message to an agent and stream the response 