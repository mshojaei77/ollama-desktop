# pip install "mcp==1.3.0"

import asyncio
import json
import os
from typing import Optional, List
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

import ollama
from dotenv import load_dotenv
import anyio

# Import the logger
from logger import app_logger

# Import LangChain memory components
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        self.exit_stack = AsyncExitStack()
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.direct_mode = False  # Flag to indicate if we're in direct chat mode
        
        # Initialize conversation memory
        self.memory = ConversationBufferMemory(return_messages=True)
        
        app_logger.info(f"MCPClient initialized with model: {self.model}")

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
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

    async def connect_to_stdio_server(self, command: str, args: list):
        """Connect to an MCP server running with STDIO transport (NPX, UV, etc.)"""
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
                return

            # List available tools to verify connection
            app_logger.info(f"Initialized {command.upper()} client...")
            app_logger.info("Listing tools...")
            response = await self.session.list_tools()
            tools = response.tools
            app_logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
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
        """Properly clean up the session and streams"""
        try:
            # Clear memory when cleaning up
            self.memory = ConversationBufferMemory(return_messages=True)
            
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
        """Process a query using Ollama and available tools"""
        # Load conversation history from memory
        memory_variables = self.memory.load_memory_variables({})
        history = memory_variables.get("history", [])
        
        # Prepare messages with history - convert LangChain messages to Ollama format
        messages = []
        
        # Add chat history if available - properly convert to Ollama format
        if history:
            for msg in history:
                # Convert LangChain message format to Ollama format
                if hasattr(msg, "type"):
                    # Handle LangChain message objects0
                    role = "assistant" if msg.type == "ai" else "user"
                    messages.append({
                        "role": role,
                        "content": msg.content
                    })
                elif isinstance(msg, dict) and "type" in msg:
                    # Handle dict format with 'type'
                    role = "assistant" if msg["type"] == "ai" else "user"
                    messages.append({
                        "role": role,
                        "content": msg["content"]
                    })
                elif isinstance(msg, dict) and "role" in msg:
                    # Messages already in proper format
                    messages.append(msg)
        
        # Add the current query
        messages.append({
            "role": "user",
            "content": query
        })

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

        available_tools = [{ 
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
        } for tool in response.tools]

        # Initial Ollama API call
        try:
            app_logger.debug(f"Sending query to Ollama model: {self.model}")
            response = ollama.chat(
                model=self.model,
                messages=messages,
                tools=available_tools
            )

            # Process response and handle tool calls
            tool_results = []
            final_text = []
            
            message = response.message
            final_text.append(message.content or "")
            
            # Check if the model wants to call a tool
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = tool_call.function.arguments
                        
                        # Execute tool call
                        app_logger.info(f"Calling tool: {tool_name} with args: {json.dumps(tool_args)}")
                        result = await self.session.call_tool(tool_name, tool_args)
                        
                        # Extract the content as a string from the result object
                        if hasattr(result, 'content'):
                            result_content = str(result.content)
                        else:
                            result_content = str(result)
                            
                        tool_results.append({"call": tool_name, "result": result_content})
                        final_text.append(f"[Calling tool {tool_name} with args {json.dumps(tool_args)}]")

                        # Add the tool response to messages
                        messages.append(message)
                        messages.append({
                            "role": "tool",
                            "content": result_content,
                            "name": tool_name
                        })

                        # Get next response from Ollama
                        app_logger.debug("Getting final response from Ollama after tool call")
                        final_response = ollama.chat(
                            model=self.model,
                            messages=messages
                        )
                        
                        final_text.append(final_response.message.content)
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        app_logger.error(error_msg)
                        final_text.append(error_msg)
                        # Continue with Ollama to get a response even if tool call failed
                        messages.append({
                            "role": "system",
                            "content": f"There was an error calling the {tool_name} tool: {str(e)}. Please respond without using the tool."
                        })
                        response = ollama.chat(
                            model=self.model,
                            messages=messages
                        )
                        final_text.append(response.message.content)
                
            result_text = "\n".join(final_text)
            
            # Store the interaction in memory
            self.memory.save_context(
                {"input": query}, 
                {"output": result_text}
            )
            
            return result_text
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
        """Process a query using Ollama directly without MCP tools"""
        # Load conversation history from memory
        memory_variables = self.memory.load_memory_variables({})
        history = memory_variables.get("history", [])
        
        # Prepare messages with history - convert LangChain messages to Ollama format
        messages = []
        
        # Add chat history if available - properly convert to Ollama format
        if history:
            for msg in history:
                # Convert LangChain message format to Ollama format
                if hasattr(msg, "type"):
                    # Handle LangChain message objects
                    role = "assistant" if msg.type == "ai" else "user"
                    messages.append({
                        "role": role,
                        "content": msg.content
                    })
                elif isinstance(msg, dict) and "type" in msg:
                    # Handle dict format with 'type'
                    role = "assistant" if msg["type"] == "ai" else "user"
                    messages.append({
                        "role": role,
                        "content": msg["content"]
                    })
                elif isinstance(msg, dict) and "role" in msg:
                    # Messages already in proper format
                    messages.append(msg)
        
        # Add the current query
        messages.append({
            "role": "user",
            "content": query
        })

        try:
            # Simple direct call to Ollama without tools
            app_logger.debug(f"Sending direct query to Ollama model: {self.model}")
            response = ollama.chat(
                model=self.model,
                messages=messages
            )
            
            result = response.message.content
            
            # Store the interaction in memory
            self.memory.save_context(
                {"input": query}, 
                {"output": result}
            )
            
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

    async def chat_loop(self):
        """Run an interactive chat loop"""
        app_logger.info("MCP Client Started!")
        if self.direct_mode:
            app_logger.info(f"Direct chat with {self.model} (no tools)")
        app_logger.info("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif not query:
                    continue
                
                app_logger.debug(f"Processing query: {query}")
                if self.direct_mode:
                    response = await self.process_direct_query(query)
                else:
                    response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                app_logger.error(f"Error in chat loop: {str(e)}")
                import traceback
                app_logger.debug(traceback.format_exc())


async def main():
    # Add a global try/finally block to ensure cleanup happens
    client = None
    try:
        # Initialize empty servers dictionary
        servers = {}
        server_types = {}
        
        # Import the config_io module and use read_ollama_config
        try:
            from config_io import read_ollama_config
            config = read_ollama_config()
            
            if config and 'mcpServers' in config:
                mcp_servers = config['mcpServers']
                for name, server in mcp_servers.items():
                    servers[name] = server
                    # Determine server type based on command
                    if 'command' in server:
                        if server['command'] in ['npx', 'npx.cmd']:
                            server_types[name] = "npx"
                        elif server['command'] in ['uvx', 'uv']:
                            server_types[name] = "uv"
                        else:
                            server_types[name] = "stdio"
                    elif 'url' in server:
                        server_types[name] = "sse"
                    else:
                        server_types[name] = "unknown"
                
                app_logger.info(f"Loaded {len(servers)} MCP servers from configuration.")
            else:
                app_logger.warning("No MCP servers found in configuration or configuration could not be loaded.")
        except ImportError:
            app_logger.error("Could not import config_io module. Please ensure it exists in the same directory.")
        except Exception as e:
            app_logger.error(f"Error loading configuration: {str(e)}")
        
        # Check if we have any servers
        if not servers:
            app_logger.warning("No MCP servers found in configuration files.")
            return
        
        # Print available options
        app_logger.info("\nAvailable options:")
        # Add "Direct chat with model" as option 0
        print("0. Direct chat with model (no MCP)")
        
        # Print MCP servers starting from index 1
        for i, name in enumerate(servers.keys(), 1):
            server_type = server_types[name]
            print(f"{i}. {name} ({server_type.upper()})")
        
        # Ask user to select a server
        selection = input("\nSelect an option (number): ")
        try:
            selection_index = int(selection)
            
            # Check if user selected the direct chat option (0)
            if selection_index == 0:
                # Direct chat mode - no MCP server required
                client = MCPClient()
                client.direct_mode = True
                app_logger.info(f"Using direct chat with {client.model} (no tools/MCP)")
                await client.chat_loop()
                return
            
            # Existing MCP server selection logic (adjusted for 1-based indexing)
            selection_index -= 1  # Adjust for 1-based indexing of servers
            selected_server = list(servers.keys())[selection_index]
            server_config = servers[selected_server]
            server_type = server_types[selected_server]
        except (ValueError, IndexError):
            app_logger.error("Invalid selection. Exiting.")
            return
        
        client = MCPClient()
        try:
            if server_type == "sse":
                server_url = server_config['url']
                app_logger.info(f"Using SSE server: {selected_server} ({server_url})")
                try:
                    await client.connect_to_sse_server(server_url=server_url)
                except Exception as e:
                    app_logger.error(f"Could not connect to SSE server: {str(e)}")
                    return
            elif server_type in ["npx", "uv", "stdio"]:
                command = server_config['command']
                args = server_config['args']
                app_logger.info(f"Using {server_type.upper()} server: {selected_server} ({command} {' '.join(args)})")
                try:
                    await client.connect_to_stdio_server(command=command, args=args)
                except Exception as e:
                    app_logger.error(f"Could not connect to {server_type.upper()} server: {str(e)}")
                    return
            
            if client.session:  # Only proceed if we have a valid session
                await client.chat_loop()
            else:
                app_logger.error("Failed to establish a valid session with the server.")
        finally:
            # Ensure cleanup happens even if there's an unhandled exception
            if client:
                app_logger.info("Cleaning up all connections...")
                await client.cleanup()
    finally:
        # Ensure cleanup happens even if there's an unhandled exception
        if client:
            app_logger.info("Cleaning up all connections...")
            await client.cleanup()


if __name__ == "__main__":
    import sys
    asyncio.run(main())