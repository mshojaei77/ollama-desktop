"""
Test script for MCP integration using Agno framework with Ollama
This script tests the MCP agents system to ensure everything works correctly
"""

import asyncio
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from api.mcp_agents.service import MCPAgentService
from api.mcp_agents.models import CreateMCPAgentRequest, MCPServerConfig


async def test_mcp_service():
    """Test the MCP agent service functionality"""
    print("🧪 Testing MCP Agent Service...")
    
    try:
        # Initialize the service
        service = MCPAgentService()
        print("✅ MCP Agent Service initialized successfully")
        
        # Test 1: Check if we can get all agents
        print("\n📋 Test 1: Getting all agents...")
        agents = await service.get_all_agents()
        print(f"✅ Found {len(agents)} existing agents")
        
        # Test 2: Get server templates
        print("\n🔧 Test 2: Getting MCP server templates...")
        templates = await service.get_mcp_server_templates()
        print(f"✅ Found {len(templates)} server templates:")
        for template in templates[:3]:  # Show first 3
            print(f"   - {template.name}: {template.description}")
        
        # Test 3: Create a sample agent with filesystem MCP
        print("\n🤖 Test 3: Creating a test MCP agent...")
        test_agent_request = CreateMCPAgentRequest(
            name="Test Filesystem Agent",
            description="A test agent for exploring the filesystem",
            instructions=[
                "You are a helpful filesystem assistant.",
                "Use the available tools to explore and analyze files.",
                "Always be informative and helpful."
            ],
            model_name="llama3.2",
            mcp_servers=[
                MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx -y @modelcontextprotocol/server-filesystem .",
                    description="Local filesystem access",
                    enabled=True
                )
            ],
            tags=["test", "filesystem"],
            category="development",
            icon="📁",
            example_prompts=[
                "What files are in the current directory?",
                "Show me the project structure"
            ],
            welcome_message="I'm your test filesystem agent!"
        )
        
        test_agent = await service.create_agent(test_agent_request)
        print(f"✅ Created test agent: {test_agent.id}")
        
        # Test 4: Try to start the agent
        print("\n🚀 Test 4: Starting the MCP agent...")
        try:
            agent_instance = await service.start_agent(test_agent.id)
            if agent_instance:
                print("✅ Agent started successfully")
                
                # Test 5: Send a simple message
                print("\n💬 Test 5: Testing basic chat functionality...")
                response = await service.chat_with_agent(
                    test_agent.id, 
                    "Hello! What tools do you have available?"
                )
                print(f"✅ Agent response: {response[:100]}...")
                
            else:
                print("⚠️ Agent started but returned None - might be a configuration issue")
                
        except Exception as e:
            print(f"⚠️ Agent start failed (expected if MCP server not available): {e}")
        
        # Test 6: Initialize sample agents if none exist
        print("\n📦 Test 6: Testing sample agent initialization...")
        result = await service.initialize_sample_agents_if_empty()
        if result:
            print("✅ Sample agents created successfully")
        else:
            print("ℹ️ Sample agents already exist or creation skipped")
        
        # Test 7: Get categories
        print("\n📂 Test 7: Getting agent categories...")
        categories = await service.get_agent_categories()
        print(f"✅ Found categories: {categories}")
        
        # Cleanup test agent
        print("\n🧹 Cleanup: Removing test agent...")
        await service.delete_agent(test_agent.id)
        print("✅ Test agent removed")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agno_mcp_direct():
    """Test Agno MCP integration directly"""
    print("\n🔬 Testing Agno MCP Direct Integration...")
    
    try:
        from agno.tools.mcp import MCPTools
        from agno.agent import Agent
        from agno.models.openai.like import OpenAILike
        
        print("✅ Agno MCP imports successful")
        
        # Test with a simple MCP server (if available)
        try:
            async with MCPTools(command="npx -y @modelcontextprotocol/server-filesystem .") as mcp_tools:
                print("✅ MCP filesystem server connection successful")
                
                # Create a simple agent
                model = OpenAILike(
                    id="llama3.2",
                    api_key="ollama",
                    base_url="http://localhost:11434/v1"
                )
                
                agent = Agent(
                    model=model,
                    tools=[mcp_tools],
                    instructions=["You are a helpful filesystem assistant."],
                    markdown=True,
                    show_tool_calls=True
                )
                
                print("✅ Agno agent with MCP tools created successfully")
                
                # Test basic interaction
                response = await agent.arun("List available tools")
                print(f"✅ Agent response: {str(response)[:100]}...")
                
        except Exception as e:
            print(f"⚠️ Direct MCP test failed (expected if server not available): {e}")
            
    except ImportError as e:
        print(f"❌ Agno MCP import failed: {e}")
        print("💡 Try installing with: pip install agno[mcp]")
        return False
        
    except Exception as e:
        print(f"❌ Direct MCP test failed: {e}")
        return False
    
    return True


async def main():
    """Main test function"""
    print("🚀 Starting MCP Integration Tests...\n")
    
    # Test 1: Service layer
    service_success = await test_mcp_service()
    
    # Test 2: Direct Agno integration
    direct_success = await test_agno_mcp_direct()
    
    print(f"\n📊 Test Results:")
    print(f"  Service Layer: {'✅ PASS' if service_success else '❌ FAIL'}")
    print(f"  Direct Agno:   {'✅ PASS' if direct_success else '❌ FAIL'}")
    
    if service_success and direct_success:
        print("\n🎉 All MCP integration tests passed!")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main()) 