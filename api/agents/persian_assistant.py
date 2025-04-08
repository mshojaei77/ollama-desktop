"""
Persian Assistant Agent

A specialized AI assistant for Persian/Farsi language support.
"""

import logging
from typing import Dict, List, Any, AsyncGenerator, Optional

from .base_agent import BaseAgent

logger = logging.getLogger("persian_assistant")

# Try to import OllamaMCPPackage, but don't fail if it's not available
try:
    from ollama_mcp import OllamaMCPPackage
except ImportError:
    logger.warning("OllamaMCPPackage not available, will use fallback mode")
    OllamaMCPPackage = None


class PersianAssistant(BaseAgent):
    """
    Persian language AI assistant for helping with Farsi queries.
    """
    
    def __init__(self):
        """Initialize the Persian assistant agent."""
        super().__init__(
            agent_id="persian-assistant",
            name="Persian Assistant",
            description="A specialized assistant for Persian/Farsi language support.",
            icon="https://picsum.photos/300",  # Placeholder icon
            tags=["persian", "farsi"],
            config={
                "default_model": "mshojaei77/gemma3persian",
                "system_message": """شما یک دستیار هوش مصنوعی مفید، خلاق و آگاه هستید. 
                شما اطلاعات دقیق در مورد طیف وسیعی از موضوعات ارائه می دهید، به کاربران در 
                انجام وظایف مختلف کمک می کنید و می توانید مکالمات معمولی داشته باشید. 
                شما طراحی شده اید تا در تمام تعاملات مفید، بی ضرر و صادق باشید.
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
                logger.info("Using fallback mode for PersianAssistant")
                self.fallback_mode = True
                return True
                
            # Initialize the Ollama chatbot
            self.chatbot = await OllamaMCPPackage.create_standalone_chatbot(
                model_name=self.config["default_model"],
                system_message=self.config["system_message"]
            )
            logger.info(f"Successfully initialized PersianAssistant with model {self.config['default_model']}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Persian assistant: {str(e)}")
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
            return f"من در حالت بازیابی کار می‌کنم. پیام شما: {message}"
            
        if not self.chatbot:
            return "متأسفم، به درستی راه‌اندازی نشده‌ام. لطفاً بعداً دوباره امتحان کنید."
        
        try:
            # Process the message with the Ollama chatbot
            response = await self.chatbot.chat(message)
            return response
        except Exception as e:
            logger.error(f"Error in Persian assistant processing: {str(e)}")
            return "هنگام پردازش درخواست شما با خطا مواجه شدم. لطفاً دوباره امتحان کنید."
    
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
            yield f"من در حالت بازیابی کار می‌کنم. پیام شما: {message}"
            return
            
        if not self.chatbot:
            yield "متأسفم، به درستی راه‌اندازی نشده‌ام. لطفاً بعداً دوباره امتحان کنید."
            return
        
        try:
            # Stream the response from the Ollama chatbot
            async for chunk in self.chatbot.chat_stream(message):
                if chunk is not None:
                    yield chunk
        except Exception as e:
            logger.error(f"Error in Persian assistant streaming: {str(e)}")
            yield "هنگام پردازش درخواست شما با خطا مواجه شدم. لطفاً دوباره امتحان کنید."
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        if self.chatbot:
            try:
                await self.chatbot.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Persian assistant: {str(e)}")
            finally:
                self.chatbot = None 