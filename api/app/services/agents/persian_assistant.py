"""
Persian Assistant Agent

A specialized AI assistant for Persian/Farsi language support.
"""

import logging
import datetime
from typing import Dict, List, Any, AsyncGenerator, Optional
import os

from .base_agent import BaseAgent

logger = logging.getLogger("persian_assistant")

def get_current_persian_date() -> str:
    """Returns the current date in the Persian (Jalali) calendar."""
    # This is a simplified example. A real implementation would use a library
    # like `jdatetime` or `persian-tools`.
    # For demonstration, we'll return a placeholder.
    # import jdatetime # Example: Use a real library if available
    # now = jdatetime.datetime.now()
    # return now.strftime("%Y/%m/%d")
    return f"امروز 29 فروردین 1404 است" # Placeholder

get_current_persian_date_tool = {
    'type': 'function',
    'function': {
        'name': 'get_current_persian_date',
        'description': 'Get the current date in the Persian (Jalali) calendar.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': [],
        },
    },
}
# --- End Example Tool ---


# Try to import OllamaMCPPackage, but don't fail if it's not available
try:
    from app.core.ollama_mcp import OllamaMCPPackage, OllamaChatbot # Added OllamaChatbot import
except ImportError:
    logger.warning("OllamaMCPPackage not available, will use fallback mode")
    OllamaMCPPackage = None
    OllamaChatbot = None # Set to None if import fails


class PersianAssistant(BaseAgent):
    """
    Persian language AI assistant for helping with Farsi queries.
    Includes an example tool to get the Persian date.
    """
    
    def __init__(self):
        """Initialize the Persian assistant agent."""
        super().__init__(
            agent_id="persian-assistant",
            name="Persian Assistant",
            description="A specialized assistant for Persian/Farsi language support.",
            icon="https://picsum.photos/300",  # Placeholder icon
            tags=["persian", "farsi"],
            example_prompts=[
                "لطفا یک شعر کوتاه فارسی بنویس",
                "درباره جاذبه‌های گردشگری ایران به من بگو",
                "چگونه می‌توانم یک غذای سنتی ایرانی درست کنم؟",
                "تاریخ امروز به شمسی چیست؟"
            ],
            config={
                "default_model": "mshojaei77/gemma3persian-tools",
                "system_message": """
                **Important:** If the user asks something you can answer with your tools (for example, the current Persian date), make sure to use the tool! After using the tool, naturally and casually include its result in your reply. Always pick the right tool for the right job, based on each tool's description.
                list of tools:
                get_current_persian_date : for getting persian (shamsi or jalali) date
                """,
            },
            # Register the tool definition with the agent
            tools=[get_current_persian_date_tool]
        )
        self.chatbot = None  # Will be OllamaChatbot when initialized
        self.fallback_mode = False

        # Register the tool implementation function
        # Ensure the name matches the 'name' in the tool definition
        self.register_tool_function("get_current_persian_date", get_current_persian_date)
        
    async def initialize(self) -> bool:
        """
        Initialize the agent and set up the Ollama chatbot.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # If OllamaMCPPackage/OllamaChatbot is not available, use fallback mode
            if OllamaMCPPackage is None or OllamaChatbot is None:
                logger.info("Using fallback mode for PersianAssistant due to missing dependencies")
                self.fallback_mode = True
                return True
                
            # Initialize the Ollama chatbot
            self.chatbot = await OllamaMCPPackage.create_standalone_chatbot(
                model_name=self.config["default_model"],
                system_message=self.config["system_message"],
                # Pass the base_url if configured, otherwise defaults inside OllamaChatbot
                base_url=os.getenv("OLLAMA_HOST") 
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
        Process a message and return a response, using tools if necessary.
        
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
            return "متأسفم، دستیار به درستی راه‌اندازی نشده است. لطفاً بعداً دوباره امتحان کنید."
        
        try:
            # Get tools and functions from the agent instance
            tools = self.get_tools()
            available_functions = self.available_functions
            
            # Process the message with the Ollama chatbot, passing tools and functions
            response = await self.chatbot.chat(
                message=message,
                tools=tools, 
                available_functions=available_functions
            )
            return response
        except Exception as e:
            logger.error(f"Error in Persian assistant processing: {str(e)}")
            return "هنگام پردازش درخواست شما با خطا مواجه شدم. لطفاً دوباره امتحان کنید."
    
    async def process_stream(self, message: str, session_id: str = None,
                           context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Process a message and stream the response, using tools if necessary.
        
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
            yield "متأسفم، دستیار به درستی راه‌اندازی نشده است. لطفاً بعداً دوباره امتحان کنید."
            return
        
        try:
            # Get tools and functions from the agent instance
            tools = self.get_tools()
            available_functions = self.available_functions

            # If any tools are registered, use the standard chat method so tool execution works correctly
            if tools:
                result = await self.chatbot.chat(message=message, tools=tools, available_functions=available_functions)
                yield result
                return

            # Stream the response from the Ollama chatbot, passing tools and functions
            async for chunk in self.chatbot.chat_stream(
                message=message,
                tools=tools,
                available_functions=available_functions
            ):
                if chunk is not None:
                    yield chunk
        except Exception as e:
            logger.error(f"Error in Persian assistant streaming: {str(e)}")
            yield "هنگام پردازش درخواست شما با خطا مواجه شدم. لطفاً دوباره امتحان کنید."
    
    async def cleanup(self) -> None:
        """Clean up resources used by the agent."""
        if self.chatbot:
            try:
                # Make sure cleanup is awaited
                await self.chatbot.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Persian assistant chatbot: {str(e)}")
            finally:
                self.chatbot = None 
        logger.info("PersianAssistant cleaned up.") 