from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from app.core.chatbot import app_logger
from typing import Optional
import asyncio
import os
import json
import re
from contextlib import AsyncExitStack

class MCPClient:
    """Client for connecting to MCP servers with Ollama integration"""

    def __init__(self, server_url: str = None, server_name: str = None, server_type: str = None, command: str = None, args: list = None):
        """
        Initialize the MCP client

        Args:
            server_url: URL for SSE servers
            server_name: Name of the server
            server_type: "sse" or "stdio"
            command: Command for STDIO servers (e.g., "npx", "uv")
            args: Arguments for STDIO servers
        """
        print(f"Initializing MCPClient for {server_name or 'unnamed server'}")
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        self.server_url = server_url
        self.server_name = server_name
        self.server_type = server_type
        self.command = command
        self.args = args or []
        self.exit_stack = AsyncExitStack()
        self.direct_mode = False  # Flag to indicate if we're in direct chat mode
        self.available_tools = []  # Store tools dynamically
        self._connected = False

    async def __aenter__(self):
        """Async context manager entry - automatically connect to server"""
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup resources"""
        await self.cleanup()

    async def _connect(self):
        """Internal method to establish connection"""
        if self._connected:
            return
            
        await self.cleanup()
        
        try:
            # Setup streams based on transport type
            if self.server_type == "sse":
                if not self.server_url:
                    raise ValueError("SSE server URL is required")
                self._streams_context = sse_client(url=self.server_url)
                transport_info = self.server_url
            elif self.server_type == "stdio":
                if not self.command or not self.args:
                    raise ValueError("STDIO server requires command and args")
                if os.name == 'nt' and self.command in ['npx', 'uv']:
                    server_params = StdioServerParameters(command='cmd.exe', args=['/c', ' '.join([self.command] + self.args)])
                else:
                    server_params = StdioServerParameters(command=self.command, args=self.args)
                self._streams_context = stdio_client(server_params)
                transport_info = f"{self.command.upper()}"
            else:
                raise ValueError(f"Unsupported server type: {self.server_type}")

            # Establish connection
            streams = await self._streams_context.__aenter__()
            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()
            
            # Initialize with timeout for STDIO
            if self.server_type == "stdio":
                await asyncio.wait_for(self.session.initialize(), timeout=10.0)
            else:
                await self.session.initialize()
            
            # Log success and list tools
            app_logger.info(f"Initialized {transport_info} client...")
            # response = await self.session.list_tools()
            # app_logger.info(f"Connected with tools: {[tool.name for tool in response.tools]}")
            self._connected = True
            
        except Exception as e:
            await self._handle_connection_error(e, self.server_type, self.server_url, self.args)
            raise

    @classmethod
    async def create(cls, server_url: str = None, server_name: str = None, server_type: str = None, command: str = None, args: list = None):
        """
        Create and connect to an MCP client
        
        Args:
            server_url: URL for SSE servers
            server_name: Name of the server
            server_type: "sse" or "stdio"
            command: Command for STDIO servers (e.g., "npx", "uv")
            args: Arguments for STDIO servers
            
        Returns:
            Connected MCPClient instance
        """
        client = cls(server_url=server_url, server_name=server_name, server_type=server_type, command=command, args=args)
        await client._connect()
        return client

    async def _handle_connection_error(self, error: Exception, server_type: str, server_url: str = None, args: list = None):
        """Handle connection errors with appropriate logging"""
        error_msg = str(error).lower()
        
        if self._is_port_in_use_error(error_msg):
            if server_type == "sse" and server_url:
                from urllib.parse import urlparse
                server_address = urlparse(server_url).netloc
                app_logger.error(f"Server at {server_address} is busy by other app or proxy")
            elif server_type == "stdio" and args:
                port_info = self._extract_port_from_args(args)
                app_logger.error(f"Local server at {port_info} is busy by other app or proxy")
        else:
            app_logger.error(f"Error connecting to {server_type.upper()} server: {str(error)}")
        
        await self.cleanup()

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
            self._connected = False
        except Exception as e:
            app_logger.error(f"Unexpected error during cleanup: {str(e)}")

    @classmethod
    async def from_config(cls, server_name: str, server_config: dict):
        """
        Create an MCP client from server configuration
        
        Args:
            server_name: Name of the server
            server_config: Server configuration dictionary
            
        Returns:
            Connected MCPClient instance
        """
        server_type = server_config.get("type", "stdio")
        
        if server_type == "sse":
            return await cls.create(
                server_url=server_config.get("url"),
                server_name=server_name,
                server_type=server_type
            )
        elif server_type == "stdio":
            return await cls.create(
                server_name=server_name,
                server_type=server_type,
                command=server_config.get("command"),
                args=server_config.get("args", [])
            )
        else:
            raise ValueError(f"Unsupported server type: {server_type}")
        
    async def list_tools(self):
        """List tools available from the MCP server"""
        if not self.session:
            raise ValueError("Not connected to an MCP server")
        return await self.session.list_tools()
    
    async def call_tool(self, tool_name: str, args: dict):
        """Call a tool on the MCP server"""
        if not self.session:
            raise ValueError("Not connected to an MCP server")
        return await self.session.call_tool(tool_name, args)
    
    async def get_tool(self, tool_name: str):
        """Get a tool from the MCP server"""
        if not self.session:
            raise ValueError("Not connected to an MCP server")
        return await self.session.get_tool(tool_name)
    
    async def list_prompts(self):
        """Get the prompt for the MCP server"""
        if not self.session:
            raise ValueError("Not connected to an MCP server")
        return await self.session.list_prompts()
    
    async def list_resources(self):
        """Get the resources for the MCP server"""
        if not self.session:
            raise ValueError("Not connected to an MCP server")
        return await self.session.list_resources()

    async def get_formatted_tool_descriptions(self) -> list:
        """Get human-readable tool descriptions for LLM prompts"""
        if not self.session:
            return []
        
        tools_result = await self.session.list_tools()
        tool_descriptions = []
        
        for tool in tools_result.tools:
            # Extract required and optional parameters
            schema = tool.inputSchema
            required_params = schema.get('required', [])
            properties = schema.get('properties', {})
            
            # Build parameter description
            param_desc = []
            for param_name, param_info in properties.items():
                param_type = param_info.get('type', 'string')
                param_desc_text = param_info.get('description', '')
                is_required = param_name in required_params
                
                param_line = f"  - {param_name} ({param_type})"
                if is_required:
                    param_line += " [REQUIRED]"
                if param_desc_text:
                    param_line += f": {param_desc_text}"
                param_desc.append(param_line)
            
            # Create tool description
            tool_desc = f"**{tool.name}** (from {self.server_name}):\n"
            tool_desc += f"  Description: {tool.description}\n"
            if param_desc:
                tool_desc += "  Parameters:\n" + "\n".join(param_desc)
            else:
                tool_desc += "  Parameters: None required"
            
            tool_descriptions.append(tool_desc)
        
        return tool_descriptions