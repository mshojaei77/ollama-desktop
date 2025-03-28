# pip install "mcp==1.3.0"

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from config_io import read_ollama_config
from ollama import ChatResponse, chat

# Optional: create a sampling callback
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="llama3.2",
        stopReason="endTurn",
    )


async def run():
    # Read server configuration from config file
    config = read_ollama_config()
    
    if not config or "mcpServers" not in config:
        print("Error: Invalid or missing configuration for MCP servers")
        return
    
    # Get the fetch server configuration
    if "fetch" not in config["mcpServers"]:
        print("Error: Missing 'fetch' server configuration")
        return
    
    fetch_config = config["mcpServers"]["fetch"]
    
    # Create server parameters from config
    server_params = StdioServerParameters(
        command=fetch_config.get("command"),
        args=fetch_config.get("args", []),
        env=fetch_config.get("env"),
    )
    
    print(f"Connecting to MCP server: {fetch_config.get('command')} {' '.join(fetch_config.get('args', []))}")
    
    try:
        async with stdio_client(server_params) as (read, write):
            print("MCP server process started")
            try:
                async with ClientSession(
                    read, write, sampling_callback=handle_sampling_message
                ) as session:
                    # Initialize the connection
                    try:
                        await session.initialize()
                        print("Connected to Fetch MCP Server successfully")
                        
                        # Example: Fetch a URL using the fetch tool
                        url = "https://en.wikipedia.org/wiki/Main_Page"
                        print(f"Fetching content from: {url}")
                        
                        result = await session.call_tool(
                            "fetch", 
                            arguments={
                                "url": url,
                                "max_length": 2000,  # Limit content length
                                "start_index": 0,    # Start from the beginning
                                "raw": False         # Convert to markdown
                            }
                        )
                        
                        if result:
                            print("Successfully fetched content:")
                            # Debug the structure of the CallToolResult object
                            print(f"Result type: {type(result)}")
                            print(f"Result attributes: {dir(result)}")
                            print(f"Result dict: {result.dict()}")
                            
                            # Access the content correctly based on the structure
                            content = result.dict().get("result", "")
                            print(f"Content length: {len(content)}")
                            print("First 200 characters:")
                            print(content[:200] + "...")
                        else:
                            print("Failed to fetch content")
                    except Exception as e:
                        print(f"Error during session initialization: {e}")
                        print(f"Error type: {type(e).__name__}")
                        import traceback
                        print(traceback.format_exc())
            except Exception as e:
                print(f"Error creating client session: {e}")
                print(f"Error type: {type(e).__name__}")
    except Exception as e:
        print(f"Error starting MCP server process: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Check if the command exists
        import shutil
        cmd = fetch_config.get('command')
        cmd_path = shutil.which(cmd)
        if cmd_path:
            print(f"Command '{cmd}' found at: {cmd_path}")
        else:
            print(f"Command '{cmd}' not found in PATH")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())