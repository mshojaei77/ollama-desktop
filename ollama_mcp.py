
# pip install "mcp==1.3.0"

import asyncio
import json
import os
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client

import ollama
from dotenv import load_dotenv
import anyio

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        self.exit_stack = AsyncExitStack()
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")

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
            print("Initialized SSE client...")
            print("Listing tools...")
            response = await self.session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
        except Exception as e:
            print(f"Error connecting to SSE server: {str(e)}")
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
                print("Initialization timed out. The server might be unresponsive.")
                await self.cleanup()
                return

            # List available tools to verify connection
            print(f"Initialized {command.upper()} client...")
            print("Listing tools...")
            response = await self.session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
        except Exception as e:
            print(f"Error connecting to STDIO server: {str(e)}")
            await self.cleanup()
            raise  # Re-raise the exception after cleanup

    async def cleanup(self):
        """Properly clean up the session and streams"""
        try:
            if self._session_context:
                try:
                    await self._session_context.__aexit__(None, None, None)
                except Exception as e:
                    print(f"Error during session cleanup: {str(e)}")
                finally:
                    self._session_context = None
            
            if self._streams_context:
                try:
                    await self._streams_context.__aexit__(None, None, None)
                except Exception as e:
                    print(f"Error during streams cleanup: {str(e)}")
                finally:
                    self._streams_context = None
                    
            # Force garbage collection to help release resources
            import gc
            gc.collect()
            
            # Reset resources
            self.session = None
        except Exception as e:
            print(f"Unexpected error during cleanup: {str(e)}")

    async def process_query(self, query: str) -> str:
        """Process a query using Ollama and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        # Try to get tools list, with reconnection logic if needed
        try:
            response = await self.session.list_tools()
        except anyio.BrokenResourceError:
            print("Connection to server lost. Attempting to reconnect...")
            # Get the current server details from the existing session
            # This is a simplified reconnection - you might need to adjust based on server type
            if hasattr(self._streams_context, 'url'):  # SSE connection
                server_url = self._streams_context.url
                await self.cleanup()
                await self.connect_to_sse_server(server_url)
            else:
                print("Unable to automatically reconnect. Please restart the client.")
                return "Connection to server lost. Please restart the client."
            
            # Try again after reconnection
            try:
                response = await self.session.list_tools()
            except Exception as e:
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
                        print(f"Calling tool: {tool_name} with args: {json.dumps(tool_args)}")
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
                        final_response = ollama.chat(
                            model=self.model,
                            messages=messages
                        )
                        
                        final_text.append(final_response.message.content)
                    except Exception as e:
                        error_msg = f"Error executing tool {tool_name}: {str(e)}"
                        print(error_msg)
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
                
            return "\n".join(final_text)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"An error occurred: {str(e)}"
    

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                elif not query:
                    continue
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
                import traceback
                traceback.print_exc()  # Print the full error traceback for debugging


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
                
                print(f"Loaded {len(servers)} MCP servers from configuration.")
            else:
                print("No MCP servers found in configuration or configuration could not be loaded.")
        except ImportError:
            print("Could not import config_io module. Please ensure it exists in the same directory.")
        except Exception as e:
            print(f"Error loading configuration: {str(e)}")
        
        # Check if we have any servers
        if not servers:
            print("No MCP servers found in configuration files.")
            return
        
        # Print available servers
        print("\nAvailable MCP servers:")
        for i, name in enumerate(servers.keys(), 1):
            server_type = server_types[name]
            print(f"{i}. {name} ({server_type.upper()})")
        
        # Ask user to select a server
        selection = input("\nSelect a server (number): ")
        try:
            index = int(selection) - 1
            selected_server = list(servers.keys())[index]
            server_config = servers[selected_server]
            server_type = server_types[selected_server]
        except (ValueError, IndexError):
            print("Invalid selection. Exiting.")
            return
        
        client = MCPClient()
        try:
            if server_type == "sse":
                server_url = server_config['url']
                print(f"Using SSE server: {selected_server} ({server_url})")
                try:
                    await client.connect_to_sse_server(server_url=server_url)
                except Exception as e:
                    print(f"Could not connect to SSE server: {str(e)}")
                    return
            elif server_type in ["npx", "uv", "stdio"]:
                command = server_config['command']
                args = server_config['args']
                print(f"Using {server_type.upper()} server: {selected_server} ({command} {' '.join(args)})")
                try:
                    await client.connect_to_stdio_server(command=command, args=args)
                except Exception as e:
                    print(f"Could not connect to {server_type.upper()} server: {str(e)}")
                    return
            
            if client.session:  # Only proceed if we have a valid session
                await client.chat_loop()
            else:
                print("Failed to establish a valid session with the server.")
        finally:
            # Ensure cleanup happens even if there's an unhandled exception
            if client:
                print("Cleaning up all connections...")
                await client.cleanup()
    finally:
        # Ensure cleanup happens even if there's an unhandled exception
        if client:
            print("Cleaning up all connections...")
            await client.cleanup()


if __name__ == "__main__":
    import sys
    asyncio.run(main())