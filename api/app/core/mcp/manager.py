from .client import MCPClient

class MCPClientManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_mcp_clients = {}
        return cls._instance

    def add_mcp_client(self, server_name: str, client: MCPClient):
        self.active_mcp_clients[server_name] = client

    def get_mcp_clients(self):
        return self.active_mcp_clients
    
    def get_mcp_client(self, server_name: str):
        return self.active_mcp_clients.get(server_name)
    
    def delete_mcp_client(self, server_name: str):
        if server_name in self.active_mcp_clients:
            del self.active_mcp_clients[server_name]
    
    async def cleanup_all_mcp_clients(self):
        for server_name in list(self.active_mcp_clients.keys()):
            await self.cleanup_mcp_client(server_name)
            del self.active_mcp_clients[server_name]
    
    async def cleanup_mcp_client(self, server_name: str):
        client = self.active_mcp_clients.get(server_name)
        if client:
            await client.cleanup() 

    async def get_all_formatted_tools(self) -> str:
        """Get formatted tool descriptions from all active clients"""
        all_descriptions = []
        
        for server_name, client in self.active_mcp_clients.items():
            descriptions = await client.get_formatted_tool_descriptions()
            all_descriptions.extend(descriptions)
        
        if all_descriptions:
            tools_section = "\n\n".join(all_descriptions)
            return f"""
                AVAILABLE TOOLS:
                {tools_section}

                TOOL USAGE INSTRUCTIONS:
                1. For action-oriented queries that require using tools, first explain what you'll do in natural language
                2. Then provide the tool call in this exact JSON format:
                {{"name": "tool_name", "arguments": {{"param_name": "value"}}}}
                3. For informational queries, provide direct answers without using tools
                4. Always use the exact tool names and required parameters as shown above
                5. When using file paths, ensure they are within allowed directories (use list_allowed_directories if unsure)
            """
        else:
            return "No tools are currently available. Provide direct answers to user queries."