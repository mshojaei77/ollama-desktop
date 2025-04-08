"""
General Purpose Assistant Agent

A versatile AI assistant for general tasks and queries.
"""

import logging
from typing import Dict, List, Any, AsyncGenerator, Optional

from .base_agent import BaseAgent

logger = logging.getLogger("general_assistant")

# Try to import OllamaMCPPackage, but don't fail if it's not available
try:
    from ollama_mcp import OllamaMCPPackage
except ImportError:
    logger.warning("OllamaMCPPackage not available, will use fallback mode")
    OllamaMCPPackage = None


class GeneralAssistant(BaseAgent):
    """
    General purpose AI assistant for a wide range of tasks.
    """
    
    def __init__(self):
        """Initialize the general assistant agent."""
        super().__init__(
            agent_id="general-assistant",
            name="General Assistant",
            description="A versatile AI assistant for answering questions and helping with various tasks.",
            icon="https://picsum.photos/300",  # Placeholder icon
            tags=["general", "utility", "question-answering"],
            config={
                "default_model": "llama3.2",
                "system_message": """You are a helpful, creative, and knowledgeable assistant. 
                You provide accurate information on a wide range of topics, help users with 
                various tasks, and can engage in casual conversation. You're designed to be 
                helpful, harmless, and honest in all interactions.
                """
            }
        )
        self.chatbot = None
        self.fallback_mode = False
        
    async def initialize(self) -> bool:
        """
        Initialize the agent and set up the Ollama chatbot.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # If OllamaMCPPackage is not available, use fallback mode
            if OllamaMCPPackage is None:
                logger.info("Using fallback mode for GeneralAssistant")
                self.fallback_mode = True
                return True
                
            # Initialize the Ollama chatbot
            self.chatbot = await OllamaMCPPackage.create_standalone_chatbot(
                model_name=self.config["default_model"],
                system_message=self.config["system_message"]
            )
            logger.info(f"Successfully initialized GeneralAssistant with model {self.config['default_model']}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize general assistant: {str(e)}")
            # Use fallback mode if chatbot initialization fails
            self.fallback_mode = True
            logger.info("Using fallback mode after initialization failure")
            return True  # Return True so the agent is still registered
    
    async def process(self, message: str, session_id: str = None, 
                     context: Dict[str, Any] = None) -> str:
        """
        Process a message and return a response.
        
        Args:
            message: The user's message
            session_id: Optional session identifier 
            context: Additional context information
            
        Returns:
            The agent's response
        """
        if self.fallback_mode:
            return f"I'm operating in fallback mode. Your message was: {message}"
            
        if not self.chatbot:
            return "Sorry, I'm not initialized properly. Please try again later."
        
        try:
            # Process the message with the Ollama chatbot
            response = await self.chatbot.chat(message)
            return response
        except Exception as e:
            logger.error(f"Error in general assistant processing: {str(e)}")
            return "I encountered an error processing your request. Please try again."
    
    async def process_stream(self, message: str, session_id: str = None,
                           context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Process a message and stream the response.
        
        Args:
            message: The user's message
            session_id: Optional session identifier
            context: Additional context information
            
        Returns:
            An async generator yielding response chunks
        """
        if self.fallback_mode:
            yield f"I'm operating in fallback mode. Your message was: {message}"
            return
            
        if not self.chatbot:
            yield "Sorry, I'm not initialized properly. Please try again later."
            return
        
        try:
            # Stream the response from the Ollama chatbot
            async for chunk in self.chatbot.chat_stream(message):
                if chunk is not None:
                    yield chunk
        except Exception as e:
            logger.error(f"Error in general assistant streaming: {str(e)}")
            yield "I encountered an error processing your request. Please try again."
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        if self.chatbot:
            try:
                await self.chatbot.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up general assistant: {str(e)}")
            finally:
                self.chatbot = None 