# pip install "mcp==1.3.0" langchain-ollama langchain-core

import asyncio
import json
import os
from typing import Optional, List, Dict, Any, Union, Callable
from contextlib import AsyncExitStack
import logging
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ChatMessage,
    FunctionMessage,
    ToolMessage,
    BaseMessage
)
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool, Tool, tool
from langchain_ollama import ChatOllama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import anyio

# Import the logger
from logger import app_logger
from .config_io import read_ollama_config

load_dotenv()  # load environment variables from .env

class BaseChatbot:
    """Base class for chatbot implementations"""
    
    def __init__(
        self,
        model_name: str = "gemma3:4b",
        system_message: Optional[str] = None,
        verbose: bool = False,
    ):
        """
        Initialize the base chatbot.
        
        Args:
            model_name: Name of the model to use
            system_message: Optional system message to set context
            verbose: Whether to output verbose logs
        """
        self.model_name = model_name
        self.system_message = system_message
        self.verbose = verbose
        self.memory = ConversationBufferMemory(return_messages=True)
        
    async def initialize(self) -> None:
        """Initialize the chatbot - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement initialize()")
    
    async def chat(self, message: str) -> str:
        """Process a chat message and return the response"""
        raise NotImplementedError("Subclasses must implement chat()")
    
    async def cleanup(self) -> None:
        """Clean up any resources used by the chatbot"""
        # Base implementation resets memory
        self.memory = ConversationBufferMemory(return_messages=True)

    def get_history(self) -> List[BaseMessage]:
        """Get the conversation history"""
        memory_variables = self.memory.load_memory_variables({})
        return memory_variables.get("history", [])
    
    def clear_history(self) -> None:
        """Clear the conversation history"""
        self.memory.clear()


class OllamaChatbot(BaseChatbot):
    """Chatbot implementation using Ollama and LangChain"""
    
    def __init__(
        self,
        model_name: str = "gemma3:4b",
        system_message: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        verbose: bool = False,
    ):
        """
        Initialize the Ollama chatbot.
        
        Args:
            model_name: Name of the Ollama model to use
            system_message: Optional system message to set context
            base_url: Base URL for the Ollama API (default: http://localhost:11434)
            temperature: Temperature parameter for generation
            top_p: Top-p parameter for generation
            verbose: Whether to output verbose logs
        """
        super().__init__(model_name, system_message, verbose)
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = temperature
        self.top_p = top_p
        self.chat_model = None
        self.ready = False
        
    async def initialize(self) -> None:
        """Initialize the Ollama chatbot"""
        try:
            # Create ChatOllama instance using latest API
            self.chat_model = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                streaming=True
            )
            
            # Test the model with a simple query to verify connection
            if self.verbose:
                app_logger.info(f"Testing connection to Ollama with model: {self.model_name}")
            
            # Updated API invocation pattern
            test_message = [HumanMessage(content="Hello, are you working? Respond in one word.")]
            test_response = await asyncio.to_thread(
                self.chat_model.invoke,
                test_message
            )
            
            if self.verbose:
                app_logger.info(f"Connection successful. Test response: {test_response.content[:50]}...")
            
            self.ready = True
            
            # Set system message if provided
            if self.system_message:
                self.memory.chat_memory.add_message(SystemMessage(content=self.system_message))
                
        except Exception as e:
            app_logger.error(f"Failed to initialize Ollama chatbot: {str(e)}")
            self.ready = False
            raise
    
    async def chat(self, message: str) -> str:
        """Process a chat message using the Ollama model"""
        if not self.ready:
            await self.initialize()
            
        if not self.ready:
            return "Chatbot is not ready. Please check the logs and try again."
            
        # Get current chat history
        history = self.get_history()
        
        # Add human message to memory
        self.memory.chat_memory.add_message(HumanMessage(content=message))
        
        try:
            # Prepare messages
            messages = history + [HumanMessage(content=message)]
            
            # Invoke the model
            response = await asyncio.to_thread(
                self.chat_model.invoke,
                messages
            )
            
            # Add the response to memory
            self.memory.chat_memory.add_message(AIMessage(content=response.content))
            
            return response.content
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            app_logger.error(error_msg)
            return error_msg
    
    async def chat_stream(self, message: str):
        """
        Process a chat message using the Ollama model and stream the responses
        
        This is an async generator that yields response chunks as they arrive
        from the model. Used for SSE and other streaming interfaces.
        """
        if not self.ready:
            await self.initialize()
            
        if not self.ready:
            yield "Chatbot is not ready. Please check the logs and try again."
            return
            
        # Get current chat history
        history = self.get_history()
        
        # Add human message to memory
        self.memory.chat_memory.add_message(HumanMessage(content=message))
        
        try:
            # Prepare messages
            messages = history + [HumanMessage(content=message)]
            
            # Get a streaming response from the model
            stream_gen = await asyncio.to_thread(
                lambda: self.chat_model.stream(messages)
            )
            
            # Initialize accumulated response to save to memory later
            full_response = ""
            
            # Stream the chunks back to the client
            async for chunk in self._aiter_from_sync_iter(stream_gen):
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    yield chunk.content
                elif isinstance(chunk, dict) and 'content' in chunk:
                    full_response += chunk['content']
                    yield chunk['content']
                elif isinstance(chunk, str):
                    full_response += chunk
                    yield chunk
            
            # Add the complete response to memory
            self.memory.chat_memory.add_message(AIMessage(content=full_response))
            
            # Yield None to indicate we're done
            yield None
            
        except Exception as e:
            error_msg = f"Error processing streaming message: {str(e)}"
            app_logger.error(error_msg)
            yield error_msg
            yield None  # Signal completion even when error occurs
    
    async def _aiter_from_sync_iter(self, sync_iter):
        """Convert a synchronous iterator to an async iterator"""
        try:
            while True:
                item = await asyncio.to_thread(next, sync_iter, StopAsyncIteration)
                if item is StopAsyncIteration:
                    break
                yield item
        except Exception as e:
            app_logger.error(f"Error in async iterator conversion: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources used by the Ollama chatbot"""
        await super().cleanup()
        self.chat_model = None
        self.ready = False


class MCPClient:
    """Client for connecting to MCP servers with Ollama integration"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the MCP client
        
        Args:
            model_name: Optional model name (defaults to OLLAMA_MODEL env var or "gemma3:4b")
        """
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        self.exit_stack = AsyncExitStack()
        self.model = model_name or os.getenv("OLLAMA_MODEL", "gemma3:4b")
        self.direct_mode = False  # Flag to indicate if we're in direct chat mode
        
        # Initialize chatbot
        self.chatbot = OllamaChatbot(model_name=self.model, verbose=True)
        
        app_logger.info(f"MCPClient initialized with model: {self.model}")

    async def connect_to_sse_server(self, server_url: str) -> bool:
        """
        Connect to an MCP server running with SSE transport
        
        Args:
            server_url: URL of the SSE server
            
        Returns:
            bool: True if connection was successful
        """
        # Ensure any previous connections are cleaned up first
        await self.cleanup()
        
        try:
            # Store the context managers so they stay alive
            self._streams_context = sse_client(url=server_url)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session: ClientSession = await self._session_context.__aenter__()

            # Initialize
            await self.session.initialize()

            # List available tools to verify connection
            app_logger.info("Initialized SSE client...")
            app_logger.info("Listing tools...")
            response = await self.session.list_tools()
            tools = response.tools
            app_logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
            
            # Initialize the chatbot
            await self.chatbot.initialize()
            
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            if self._is_port_in_use_error(error_msg):
                # Extract server URL parts to show in the error message
                from urllib.parse import urlparse
                parsed_url = urlparse(server_url)
                server_address = f"{parsed_url.netloc}"
                app_logger.error(f"Your local server at {server_address} is busy by other app or proxy")
            else:
                app_logger.error(f"Error connecting to SSE server: {str(e)}")
            await self.cleanup()
            raise  # Re-raise the exception after cleanup

    async def connect_to_stdio_server(self, command: str, args: list) -> bool:
        """
        Connect to an MCP server running with STDIO transport (NPX, UV, etc.)
        
        Args:
            command: Command to run (e.g., "npx", "uv")
            args: Arguments to pass to the command
            
        Returns:
            bool: True if connection was successful
        """
        # Ensure any previous connections are cleaned up first
        await self.cleanup()
        
        try:
            # On Windows, we need to use cmd.exe to run npx
            if os.name == 'nt' and command in ['npx', 'uv']:
                # Convert the command and args to a single command string for cmd.exe
                cmd_args = ' '.join([command] + args)
                server_params = StdioServerParameters(
                    command='cmd.exe',
                    args=['/c', cmd_args]
                )
            else:
                # For non-Windows systems or other commands
                server_params = StdioServerParameters(command=command, args=args)
            
            # Store the context managers so they stay alive
            self._streams_context = stdio_client(server_params)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session: ClientSession = await self._session_context.__aenter__()

            # Initialize with timeout
            try:
                await asyncio.wait_for(self.session.initialize(), timeout=10.0)
            except asyncio.TimeoutError:
                app_logger.error("Initialization timed out. The server might be unresponsive.")
                await self.cleanup()
                return False

            # List available tools to verify connection
            app_logger.info(f"Initialized {command.upper()} client...")
            app_logger.info("Listing tools...")
            response = await self.session.list_tools()
            tools = response.tools
            app_logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
            
            # Initialize the chatbot
            await self.chatbot.initialize()
            
            return True
            
        except Exception as e:
            error_msg = str(e).lower()
            if self._is_port_in_use_error(error_msg):
                # Try to extract port information from command args
                port_info = self._extract_port_from_args(args)
                app_logger.error(f"Your local server at {port_info} is busy by other app or proxy")
            else:
                app_logger.error(f"Error connecting to STDIO server: {str(e)}")
            await self.cleanup()
            raise  # Re-raise the exception after cleanup

    def _is_port_in_use_error(self, error_message: str) -> bool:
        """Helper method to detect if an error is related to port conflicts"""
        port_conflict_indicators = [
            "address already in use",
            "port already in use", 
            "address in use",
            "eaddrinuse",
            "connection refused",
            "cannot bind to address",
            "failed to listen on"
        ]
        
        error_message = error_message.lower()
        return any(indicator in error_message for indicator in port_conflict_indicators)

    def _extract_port_from_args(self, args: list) -> str:
        """Try to extract port information from command args"""
        # Common patterns for port specification in command line args
        port = "unknown port"
        
        for i, arg in enumerate(args):
            if arg == "--port" and i + 1 < len(args):
                port = args[i + 1]
                break
            elif arg.startswith("--port="):
                port = arg.split("=", 1)[1]
                break
            elif arg == "-p" and i + 1 < len(args):
                port = args[i + 1]
                break
        
        return port

    async def cleanup(self):
        """
        Properly clean up the session and streams
        
        Returns:
            None
        """
        try:
            # Clean up the chatbot
            if hasattr(self, 'chatbot') and self.chatbot:
                await self.chatbot.cleanup()
            
            if self._session_context:
                try:
                    await self._session_context.__aexit__(None, None, None)
                except Exception as e:
                    app_logger.error(f"Error during session cleanup: {str(e)}")
                finally:
                    self._session_context = None
            
            if self._streams_context:
                try:
                    await self._streams_context.__aexit__(None, None, None)
                except Exception as e:
                    app_logger.error(f"Error during streams cleanup: {str(e)}")
                finally:
                    self._streams_context = None
                    
            # Force garbage collection to help release resources
            import gc
            gc.collect()
            
            # Reset resources
            self.session = None
        except Exception as e:
            app_logger.error(f"Unexpected error during cleanup: {str(e)}")

    async def process_query(self, query: str) -> str:
        """
        Process a query using Ollama and available tools
        
        Args:
            query: The query text to process
            
        Returns:
            str: Response text
        """
        # Try to get tools list, with reconnection logic if needed
        try:
            response = await self.session.list_tools()
        except anyio.BrokenResourceError:
            app_logger.warning("Connection to server lost. Attempting to reconnect...")
            # Get the current server details from the existing session
            # This is a simplified reconnection - you might need to adjust based on server type
            if hasattr(self._streams_context, 'url'):  # SSE connection
                server_url = self._streams_context.url
                await self.cleanup()
                await self.connect_to_sse_server(server_url)
            else:
                app_logger.error("Unable to automatically reconnect. Please restart the client.")
                return "Connection to server lost. Please restart the client."
            
            # Try again after reconnection
            try:
                response = await self.session.list_tools()
            except Exception as e:
                app_logger.error(f"Failed to reconnect to server: {str(e)}")
                return f"Failed to reconnect to server: {str(e)}"

        available_tools = response.tools
        
        try:
            # Generate initial response with the chatbot
            app_logger.debug(f"Processing query with Ollama model: {self.model}")
            initial_result = await self.chatbot.chat(query)
            
            # Check for potential tool calls in the response
            tool_results = []
            final_text = [initial_result]
            
            # Extract potential tool calls from the text
            # This is a simplified approach - for production use, you'd use a more robust parser
            import re
            tool_call_pattern = r"\{\s*\"name\":\s*\"([^\"]+)\"\s*,\s*\"arguments\":\s*(\{[^}]+\})\s*\}"
            matches = re.findall(tool_call_pattern, initial_result)
            
            # Process any tool calls found
            for tool_name, args_str in matches:
                try:
                    # Parse the arguments
                    tool_args = json.loads(args_str)
                    
                    # Check if this tool exists
                    if any(tool.name == tool_name for tool in available_tools):
                        # Execute tool call
                        app_logger.info(f"Calling tool: {tool_name} with args: {json.dumps(tool_args)}")
                        result = await self.session.call_tool(tool_name, tool_args)
                        
                        # Extract the content as a string from the result object
                        if hasattr(result, 'content'):
                            result_content = str(result.content)
                        else:
                            result_content = str(result)
                            
                        tool_results.append({"call": tool_name, "result": result_content})
                        final_text.append(f"[Called tool {tool_name} with result: {result_content}]")
                        
                        # Get final response about the tool result
                        follow_up = f"The tool {tool_name} returned: {result_content}. Please provide your final answer based on this information."
                        final_response = await self.chatbot.chat(follow_up)
                        final_text.append(final_response)
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    app_logger.error(error_msg)
                    final_text.append(error_msg)
            
            return "\n".join(final_text)
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for server connection issues (502 status code)
            if "status code: 502" in error_msg:
                # Extract server information from environment
                server_url = os.getenv("OLLAMA_HOST", "localhost:11434")
                error_message = f"Your local Ollama server at {server_url} is busy by other app or proxy"
                app_logger.error(f"Error in process_query: {error_message}")
                return error_message
            
            # For other errors, log the full error
            app_logger.error(f"Error in process_query: {error_msg}")
            return f"An error occurred: {error_msg}"

    async def process_direct_query(self, query: str) -> str:
        """
        Process a query using Ollama directly without MCP tools
        
        Args:
            query: The query text to process
            
        Returns:
            str: Response text
        """
        try:
            # Use the chatbot for direct querying
            result = await self.chatbot.chat(query)
            return result
        except Exception as e:
            error_msg = str(e)
            
            # Check for server connection issues (502 status code)
            if "status code: 502" in error_msg:
                # Extract server information from environment
                server_url = os.getenv("OLLAMA_HOST", "localhost:11434")
                error_message = f"Your local Ollama server at {server_url} is busy by other app or proxy"
                app_logger.error(f"Error in process_direct_query: {error_message}")
                return error_message
            
            # For other errors, log the full error
            app_logger.error(f"Error in process_direct_query: {error_msg}")
            return f"An error occurred: {error_msg}"


class OllamaMCPPackage:
    """Main package class for using Ollama with MCP"""
    
    @staticmethod
    async def create_client(model_name: str = None) -> MCPClient:
        """
        Create and return a new MCP client
        
        Args:
            model_name: Optional model name to use
            
        Returns:
            MCPClient: Initialized client
        """
        return MCPClient(model_name=model_name)
    
    @staticmethod
    async def create_standalone_chatbot(
        model_name: str = "gemma3:4b",
        system_message: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7
    ) -> OllamaChatbot:
        """
        Create and initialize a standalone Ollama chatbot
        
        Args:
            model_name: Name of the Ollama model to use
            system_message: Optional system message to set context
            base_url: Base URL for the Ollama API
            temperature: Temperature parameter for generation
            
        Returns:
            OllamaChatbot: Initialized chatbot
        """
        chatbot = OllamaChatbot(
            model_name=model_name,
            system_message=system_message,
            base_url=base_url,
            temperature=temperature
        )
        await chatbot.initialize()
        return chatbot
    
    @staticmethod
    async def get_available_models(base_url: Optional[str] = None) -> List[str]:
        """
        Get a list of available Ollama models
        
        Args:
            base_url: Optional base URL for the Ollama API
            
        Returns:
            List[str]: List of available model names
        """
        import requests
        
        try:
            base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
            response = requests.get(f"{base_url}/api/tags")
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            app_logger.error(f"Error getting available models: {str(e)}")
            return []
    
    @staticmethod
    async def load_mcp_config() -> Dict[str, Any]:
        """
        Load MCP server configuration
        
        Returns:
            Dict[str, Any]: Configuration dictionary with server information
        """
        try:
            from config_io import read_ollama_config
            config = read_ollama_config()
            
            if config and 'mcpServers' in config:
                return config
            else:
                app_logger.warning("No MCP servers found in configuration or configuration could not be loaded.")
                return {"mcpServers": {}}
        except ImportError:
            app_logger.error("Could not import config_io module. Please ensure it exists in the same directory.")
            return {"mcpServers": {}}
        except Exception as e:
            app_logger.error(f"Error loading configuration: {str(e)}")
            return {"mcpServers": {}}

    @staticmethod
    async def get_mcp_server_config(server_name):
        """Get MCP server configuration by name"""
        if not server_name:
            return None
        
        try:
            config = await read_ollama_config()
            if not config or "mcpServers" not in config:
                app_logger.warning("MCP servers configuration not found or empty.")
                return None
            
            server_conf = config["mcpServers"].get(server_name)
            if not server_conf:
                app_logger.warning(f"Configuration for MCP server '{server_name}' not found.")
            return server_conf
        except Exception as e:
            app_logger.error(f"Error getting MCP server config for '{server_name}': {str(e)}")
            return None