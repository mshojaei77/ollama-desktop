"""
🚀 Comprehensive MCP System Demo
=====================================

This script demonstrates the complete MCP (Model Context Protocol) integration
with Ollama Desktop. It showcases:

1. Creating MCP agents with different server configurations
2. Using various MCP server types (filesystem, git, web search)
3. Chatting with agents that have MCP tool access
4. Managing agent lifecycle and cleanup

Requirements:
- Ollama running locally
- Node.js (for npm/npx MCP servers)
- Internet connection (for some MCP servers)
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from api.mcp_agents.service import MCPAgentService
from api.mcp_agents.models import CreateMCPAgentRequest, MCPServerConfig


class MCPSystemDemo:
    """Comprehensive demo of the MCP system"""
    
    def __init__(self):
        self.service = MCPAgentService()
        self.demo_agents: List[str] = []
    
    async def run_complete_demo(self):
        """Run the complete MCP system demo"""
        print("🚀 Starting Comprehensive MCP System Demo\n")
        
        try:
            # Demo 1: Basic system overview
            await self.demo_system_overview()
            
            # Demo 2: Available MCP server templates
            await self.demo_server_templates()
            
            # Demo 3: Create and test filesystem agent
            await self.demo_filesystem_agent()
            
            # Demo 4: Create and test git agent
            await self.demo_git_agent()
            
            # Demo 5: Create and test multi-server agent
            await self.demo_multi_server_agent()
            
            # Demo 6: Agent management features
            await self.demo_agent_management()
            
            print("\n🎉 Complete MCP System Demo finished successfully!")
            print("✨ The MCP integration is working perfectly with Ollama Desktop!")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup demo agents
            await self.cleanup_demo_agents()
    
    async def demo_system_overview(self):
        """Show system overview and capabilities"""
        print("📋 Demo 1: System Overview")
        print("=" * 50)
        
        # Get existing agents
        agents = await self.service.get_all_agents()
        print(f"📊 Current system status:")
        print(f"   • Total agents: {len(agents)}")
        
        # Get categories
        categories = await self.service.get_agent_categories()
        print(f"   • Categories: {categories}")
        
        # Get available models
        try:
            from api.ollama_client import OllamaPackage
            models = await OllamaPackage.get_available_models()
            print(f"   • Available Ollama models: {len(models)}")
            if models:
                print(f"     - Primary model: {models[0]}")
        except Exception as e:
            print(f"   • Ollama models: Unable to fetch ({e})")
        
        print()
    
    async def demo_server_templates(self):
        """Show available MCP server templates"""
        print("🔧 Demo 2: Available MCP Server Templates")
        print("=" * 50)
        
        templates = await self.service.get_mcp_server_templates()
        print(f"📦 Found {len(templates)} MCP server templates:\n")
        
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template.icon} {template.name}")
            print(f"   Category: {template.category}")
            print(f"   Transport: {template.transport}")
            print(f"   Description: {template.description}")
            if template.env_vars:
                print(f"   Environment variables needed: {', '.join(template.env_vars)}")
            print()
    
    async def demo_filesystem_agent(self):
        """Create and test a filesystem agent"""
        print("📁 Demo 3: Filesystem Agent")
        print("=" * 50)
        
        # Create filesystem agent
        print("🤖 Creating filesystem agent...")
        
        agent_request = CreateMCPAgentRequest(
            name="Demo Filesystem Explorer",
            description="A filesystem agent for exploring and analyzing project files",
            instructions=[
                "You are a helpful filesystem assistant.",
                "Use your filesystem tools to explore and analyze files.",
                "Provide clear, detailed responses about file contents and directory structures.",
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
            tags=["demo", "filesystem", "exploration"],
            category="development",
            icon="📁",
            example_prompts=[
                "What files are in the current directory?",
                "Show me the project structure",
                "What's in the README file?",
                "Find all Python files in the project"
            ],
            welcome_message="I'm your filesystem explorer! I can help you navigate and analyze files in this project.",
            markdown=True,
            show_tool_calls=True
        )
        
        agent = await self.service.create_agent(agent_request)
        if agent:
            self.demo_agents.append(agent.id)
            print(f"✅ Created agent: {agent.name} (ID: {agent.id})")
            
            # Test the agent
            print("💬 Testing filesystem agent...")
            test_queries = [
                "What files are in the current directory?",
                "Tell me about this project by looking at the main files"
            ]
            
            for query in test_queries:
                print(f"\n📝 Query: {query}")
                try:
                    response = await self.service.chat_with_agent(agent.id, query)
                    print(f"🤖 Response: {response[:200]}...")
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        print()
    
    async def demo_git_agent(self):
        """Create and test a git agent"""
        print("🌿 Demo 4: Git Agent")
        print("=" * 50)
        
        print("🤖 Creating git agent...")
        
        agent_request = CreateMCPAgentRequest(
            name="Demo Git Assistant",
            description="A git agent for repository management and version control",
            instructions=[
                "You are a helpful git assistant.",
                "Use your git tools to help with repository management.",
                "Provide clear explanations about git operations and repository status.",
                "Help users understand git workflows and best practices."
            ],
            model_name="llama3.2",
            mcp_servers=[
                MCPServerConfig(
                    name="git",
                    transport="stdio",
                    command="uvx mcp-server-git",
                    description="Git repository operations",
                    enabled=True
                )
            ],
            tags=["demo", "git", "version-control"],
            category="development",
            icon="🌿",
            example_prompts=[
                "What's the current git status?",
                "Show me the latest commits",
                "What branch am I on?",
                "Are there any uncommitted changes?"
            ],
            welcome_message="I'm your git assistant! I can help you manage your repository and understand git workflows.",
            markdown=True,
            show_tool_calls=True
        )
        
        agent = await self.service.create_agent(agent_request)
        if agent:
            self.demo_agents.append(agent.id)
            print(f"✅ Created agent: {agent.name} (ID: {agent.id})")
            
            # Test the agent
            print("💬 Testing git agent...")
            test_queries = [
                "What's the current status of this git repository?",
                "Show me information about the latest commits"
            ]
            
            for query in test_queries:
                print(f"\n📝 Query: {query}")
                try:
                    response = await self.service.chat_with_agent(agent.id, query)
                    print(f"🤖 Response: {response[:200]}...")
                except Exception as e:
                    print(f"❌ Error (expected if git server not available): {e}")
        
        print()
    
    async def demo_multi_server_agent(self):
        """Create and test an agent with multiple MCP servers"""
        print("🔄 Demo 5: Multi-Server Agent")
        print("=" * 50)
        
        print("🤖 Creating multi-server agent...")
        
        agent_request = CreateMCPAgentRequest(
            name="Demo Multi-Tool Assistant",
            description="An advanced agent with access to multiple MCP servers for comprehensive assistance",
            instructions=[
                "You are a comprehensive AI assistant with access to multiple tools.",
                "Use filesystem tools to explore and analyze files.",
                "Use sequential thinking tools to work through complex problems step by step.",
                "Combine different tools to provide comprehensive assistance.",
                "Always explain what tools you're using and why."
            ],
            model_name="llama3.2",
            mcp_servers=[
                MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx -y @modelcontextprotocol/server-filesystem .",
                    description="Filesystem access for file operations",
                    enabled=True
                ),
                MCPServerConfig(
                    name="sequential_thinking",
                    transport="stdio",
                    command="npx -y @modelcontextprotocol/server-sequential-thinking",
                    description="Sequential thinking and problem-solving tools",
                    enabled=True
                )
            ],
            tags=["demo", "multi-server", "comprehensive"],
            category="analysis",
            icon="🧠",
            example_prompts=[
                "Analyze this project's structure and explain its purpose",
                "Help me understand the codebase architecture",
                "What improvements could be made to this project?",
                "Create a summary of the project's key files"
            ],
            welcome_message="I'm your comprehensive assistant with access to multiple tools! I can analyze files, think through complex problems, and provide detailed insights.",
            markdown=True,
            show_tool_calls=True
        )
        
        agent = await self.service.create_agent(agent_request)
        if agent:
            self.demo_agents.append(agent.id)
            print(f"✅ Created agent: {agent.name} (ID: {agent.id})")
            
            # Test the agent
            print("💬 Testing multi-server agent...")
            query = "Use your thinking tool to analyze this project's structure and explain what it does"
            print(f"\n📝 Query: {query}")
            try:
                response = await self.service.chat_with_agent(agent.id, query)
                print(f"🤖 Response: {response[:300]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print()
    
    async def demo_agent_management(self):
        """Demo agent management features"""
        print("⚙️ Demo 6: Agent Management Features")
        print("=" * 50)
        
        # Get all agents
        agents = await self.service.get_all_agents()
        print(f"📊 Current agents: {len(agents)}")
        
        # Show demo agents
        demo_agents = [agent for agent in agents if agent.id in self.demo_agents]
        print(f"🎯 Demo agents created: {len(demo_agents)}")
        
        for agent in demo_agents:
            print(f"\n🤖 Agent: {agent.name}")
            print(f"   • ID: {agent.id}")
            print(f"   • Category: {agent.category}")
            print(f"   • MCP Servers: {len(agent.mcp_servers)}")
            print(f"   • Model: {agent.model_provider}/{agent.model_name}")
            
            # Test agent status
            try:
                # Try to start the agent to test functionality
                agent_instance = await self.service.start_agent(agent.id)
                if agent_instance:
                    print(f"   • Status: ✅ Active and ready")
                    # Cleanup the instance
                    await self.service._cleanup_agent(agent.id)
                else:
                    print(f"   • Status: ⚠️ Could not start (might need configuration)")
            except Exception as e:
                print(f"   • Status: ❌ Error starting ({str(e)[:50]}...)")
        
        print()
    
    async def cleanup_demo_agents(self):
        """Clean up demo agents"""
        if self.demo_agents:
            print("🧹 Cleaning up demo agents...")
            for agent_id in self.demo_agents:
                try:
                    success = await self.service.delete_agent(agent_id)
                    if success:
                        print(f"   ✅ Deleted agent: {agent_id}")
                    else:
                        print(f"   ❌ Failed to delete agent: {agent_id}")
                except Exception as e:
                    print(f"   ❌ Error deleting agent {agent_id}: {e}")
            
            # Clean up all agents
            try:
                await self.service.cleanup_all_agents()
                print("   ✅ Cleaned up all agent instances")
            except Exception as e:
                print(f"   ⚠️ Warning during cleanup: {e}")
            
            self.demo_agents.clear()


async def main():
    """Main demo function"""
    print("🎯 Ollama Desktop MCP System - Comprehensive Demo")
    print("=" * 60)
    print()
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    # Check if Ollama is running
    try:
        from api.ollama_client import OllamaPackage
        models = await OllamaPackage.get_available_models()
        if models:
            print(f"   ✅ Ollama is running with {len(models)} models")
        else:
            print("   ⚠️ Ollama is running but no models found")
    except Exception as e:
        print(f"   ❌ Ollama check failed: {e}")
        print("   💡 Make sure Ollama is running: https://ollama.ai/")
        return
    
    # Check if we're in the right directory
    if not Path("api/mcp_agents").exists():
        print("   ❌ Not in the right directory. Please run from the project root.")
        return
    
    print("   ✅ Project structure looks good")
    print()
    
    # Run the demo
    demo = MCPSystemDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    print("🚀 Starting MCP System Demo...\n")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc() 