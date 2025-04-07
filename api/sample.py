# Create server parameters for stdio connection
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from langchain_ollama import ChatOllama
model = ChatOllama(model="llama3.2")

server_params = StdioServerParameters(
    command="uvx",
    # Make sure to update to the full absolute path to your math_server.py file
    args=["mcp-server-calculator"],
)

async def main():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # Get tools
            tools = await load_mcp_tools(session)
            print("Available tools:")
            for tool in tools:
                print(f"- {tool.name}: {tool.description}")
            print()

            # Create and run the agent
            print("Running calculation query...")
            agent = create_react_agent(model, tools)
            agent_response = await agent.ainvoke({"messages": "what's (3 + 5) x 12?"})
            
            print("\nAgent conversation:")
            for message in agent_response["messages"]:
                if hasattr(message, "content") and message.content:
                    print(f"{message.__class__.__name__}: {message.content}")
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        print(f"Tool call: {tool_call}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())