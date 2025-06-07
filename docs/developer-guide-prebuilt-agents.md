# Developer Guide: Building Pre-built MCP Agents

> A comprehensive guide for developers on how to create and ship pre-built MCP agents with Ollama Desktop.

## Overview

Pre-built MCP agents are ready-to-use agents that ship with the Ollama Desktop application. They provide users with immediate value and demonstrate the capabilities of the MCP integration. Unlike user-created agents (built through the UI), pre-built agents are defined in code and automatically initialized when the application starts.

## Key Concepts

### Pre-built vs User-created Agents

| Type | Description | Source | Tags |
|------|-------------|---------|------|
| **Pre-built** | Shipped with the application | Code-defined templates | Always includes `"prebuilt"` tag |
| **User-created** | Created through the UI | User interface | No `"prebuilt"` tag |

Both types function identically - the distinction is purely organizational and helps users understand which agents are ready-to-use versus custom-built.

## Architecture

### File Structure

```
api/mcp_agents/
├── service.py          # Main service logic
├── models.py           # Data models
├── routes.py           # API endpoints
└── __init__.py

front/src/renderer/src/assets/agents/
└── filesystem.png      # Agent icons
```

### Core Components

1. **AgentTemplate**: Defines the structure of pre-built agents
2. **MCPAgentService**: Handles agent lifecycle and creation
3. **API Routes**: Expose pre-built agent functionality

## Adding a New Pre-built Agent

### Step 1: Define the Agent Template

Edit `api/mcp_agents/service.py` and add your agent to the `_get_prebuilt_agent_templates()` method:

```python
def _get_prebuilt_agent_templates(self) -> List[AgentTemplate]:
    """Get predefined pre-built agent templates (shipped with the application)"""
    return [
        # Existing Filesystem Explorer Agent
        AgentTemplate(
            name="Filesystem Explorer",
            description="Explore and analyze files and directories with detailed insights",
            category="development",
            instructions=[
                "You are a filesystem assistant that helps users explore files and directories.",
                "Navigate the filesystem to answer questions about project structure and content.",
                "Use the list_allowed_directories tool to find accessible directories.",
                "Provide clear context about files you examine.",
                "Be concise and focus on relevant information.",
                "Use headings to organize your responses for better readability."
            ],
            mcp_servers=[
                MCPServerConfig(
                    name="filesystem",
                    transport="stdio",
                    command="npx -y @modelcontextprotocol/server-filesystem .",
                    enabled=True,
                    description="Access to local filesystem for reading and exploring files"
                )
            ],
            tags=["filesystem", "development", "analysis"],
            icon="./front/src/renderer/src/assets/agents/filesystem.png",
            example_prompts=[
                "What files are in the current directory?",
                "Show me the project structure",
                "Find all Python files in this project",
                "What's in the README file?",
                "Analyze the project's dependencies"
            ],
            welcome_message="I'm your filesystem explorer! I can help you navigate, analyze, and understand your project structure and files. What would you like to explore today?"
        ),
        
        # ADD YOUR NEW AGENT HERE
        AgentTemplate(
            name="🌐 Web Search Assistant",
            description="Search the web for current information and answer questions using real-time data",
            category="research",
            instructions=[
                "You are a web search assistant that helps users find current information.",
                "Use web search tools to get up-to-date information on any topic.",
                "Provide accurate, well-sourced responses with relevant links.",
                "Always cite your sources and indicate when information is current.",
                "Be helpful and thorough in your research."
            ],
            mcp_servers=[
                MCPServerConfig(
                    name="web_search",
                    transport="stdio",
                    command="npx -y @modelcontextprotocol/server-brave-search",
                    enabled=True,
                    description="Web search capabilities for current information",
                    env={"BRAVE_API_KEY": ""}  # User will need to configure
                )
            ],
            tags=["web", "search", "research", "current-info"],
            icon="./front/src/renderer/src/assets/agents/web-search.png",
            example_prompts=[
                "What's the latest news about AI developments?",
                "Search for information about renewable energy trends",
                "Find current stock market information",
                "What are the latest web development best practices?"
            ],
            welcome_message="I'm your web search assistant! I can help you find current information on any topic. What would you like to research today?"
        )
    ]
```

### Step 2: Create Agent Icon (Optional)

Add an icon for your agent in `front/src/renderer/src/assets/agents/`:

```bash
# Add your icon file
front/src/renderer/src/assets/agents/web-search.png
```

**Icon Requirements:**
- Format: PNG, SVG, or JPG
- Size: 64x64px or larger (square aspect ratio)
- Style: Should match the application's design language
- Fallback: If no icon is provided, emoji or default icon will be used

### Step 3: Test Your Agent

Create a test script to verify your agent:

```python
# test_new_prebuilt_agent.py
import asyncio
from api.mcp_agents.service import MCPAgentService

async def test_new_agent():
    service = MCPAgentService()
    
    # Create pre-built agents
    agents = await service.create_prebuilt_agents()
    
    # Find your new agent
    web_agent = next((a for a in agents if "Web Search" in a.name), None)
    if web_agent:
        print(f"✅ Created: {web_agent.name}")
        print(f"Icon: {web_agent.icon}")
        print(f"Tags: {web_agent.tags}")
    else:
        print("❌ Agent not found")

if __name__ == "__main__":
    asyncio.run(test_new_agent())
```

## Best Practices

### 1. Agent Design Principles

**Clear Purpose**: Each agent should have a specific, well-defined purpose
```python
# ✅ Good - Specific purpose
name="📊 Data Analysis Assistant"
description="Analyze CSV files and generate insights with visualizations"

# ❌ Bad - Too vague
name="🤖 General Helper"
description="Helps with various tasks"
```

**Useful Instructions**: Provide clear, actionable instructions
```python
# ✅ Good - Specific, actionable instructions
instructions=[
    "You are a data analysis assistant specialized in CSV file analysis.",
    "Always start by examining the data structure and column types.",
    "Provide summary statistics before diving into detailed analysis.",
    "Create visualizations when they help explain insights.",
    "Explain your analysis process step by step."
]

# ❌ Bad - Vague instructions
instructions=[
    "You are helpful.",
    "Answer questions about data."
]
```

### 2. MCP Server Configuration

**Use Reliable Servers**: Only include well-tested, stable MCP servers
```python
# ✅ Good - Official, stable server
command="npx -y @modelcontextprotocol/server-filesystem ."

# ⚠️ Caution - Third-party server (verify stability)
command="npx -y some-third-party-server"
```

**Handle Dependencies**: Clearly indicate external dependencies
```python
# Environment variables that users need to configure
env={"API_KEY": ""}  # Clear indication that config is needed

# Document in description
description="Requires API key configuration for external service access"
```

### 3. Tags and Categories

**Use Consistent Tags**:
- `"development"` - For coding, git, filesystem tools
- `"research"` - For search, analysis, information gathering
- `"productivity"` - For task management, scheduling, organization
- `"analysis"` - For data analysis, reporting, insights
- `"communication"` - For email, messaging, social tools

**Choose Appropriate Categories**:
- `"development"` - Developer tools
- `"research"` - Information gathering
- `"productivity"` - Task and workflow management
- `"analysis"` - Data analysis and reporting
- `"communication"` - Messaging and collaboration
- `"content"` - Content creation and management

### 4. Example Prompts

Provide 3-5 diverse, realistic example prompts:
```python
example_prompts=[
    "What files are in the current directory?",           # Basic usage
    "Show me the project structure",                      # Common task
    "Find all Python files in this project",             # Specific search
    "What's in the README file?",                         # File inspection
    "Analyze the project's dependencies"                  # Advanced analysis
]
```

### 5. Welcome Messages

Create engaging, helpful welcome messages:
```python
# ✅ Good - Specific, welcoming, actionable
welcome_message="I'm your filesystem explorer! I can help you navigate, analyze, and understand your project structure and files. What would you like to explore today?"

# ❌ Bad - Generic, not helpful
welcome_message="Hello! I'm an AI assistant."
```

## Testing and Validation

### Unit Testing

```python
import pytest
from api.mcp_agents.service import MCPAgentService

@pytest.mark.asyncio
async def test_prebuilt_agents_creation():
    service = MCPAgentService()
    
    # Test template retrieval
    templates = service._get_prebuilt_agent_templates()
    assert len(templates) > 0
    
    # Test agent creation
    agents = await service.create_prebuilt_agents()
    assert len(agents) > 0
    
    # Test prebuilt tag
    for agent in agents:
        assert "prebuilt" in agent.tags

@pytest.mark.asyncio
async def test_agent_distinction():
    service = MCPAgentService()
    
    prebuilt = await service.get_prebuilt_agents()
    user_created = await service.get_user_created_agents()
    
    # Ensure proper separation
    for agent in prebuilt:
        assert "prebuilt" in agent.tags
    
    for agent in user_created:
        assert "prebuilt" not in agent.tags
```

### Integration Testing

```python
async def test_agent_functionality():
    service = MCPAgentService()
    
    # Create agents
    agents = await service.create_prebuilt_agents()
    
    # Test each agent
    for agent in agents:
        try:
            # Start agent
            instance = await service.start_agent(agent.id)
            assert instance is not None
            
            # Test basic chat
            response = await service.chat_with_agent(
                agent.id, 
                "Hello, what can you help me with?"
            )
            assert response is not None
            assert len(response) > 0
            
        except Exception as e:
            pytest.fail(f"Agent {agent.name} failed: {e}")
```

## API Endpoints

Pre-built agents expose these additional endpoints:

```python
# Get all pre-built agents
GET /mcp-agents/prebuilt

# Get all user-created agents  
GET /mcp-agents/user-created

# Initialize pre-built agents (if none exist)
POST /mcp-agents/initialize-prebuilt

# Force create pre-built agents
POST /mcp-agents/create-prebuilt
```

## Deployment Checklist

Before deploying pre-built agents:

- [ ] Agent template is properly defined
- [ ] Icon is added (if using custom icon)
- [ ] Instructions are clear and specific
- [ ] MCP server dependencies are documented
- [ ] Environment variables are clearly marked
- [ ] Example prompts are realistic and diverse
- [ ] Welcome message is engaging and helpful
- [ ] Tags and categories are appropriate
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Example: Complete Web Search Agent

Here's a complete example of a well-designed pre-built agent:

```python
AgentTemplate(
    name="🌐 Web Search Assistant",
    description="Search the web for current information and provide well-sourced, up-to-date answers on any topic",
    category="research",
    instructions=[
        "You are a web search assistant that helps users find current information.",
        "Always use web search tools to get the most up-to-date information.",
        "Provide accurate, well-sourced responses with relevant links when available.",
        "Cite your sources and indicate when information was last updated.",
        "Be thorough but concise in your research and explanations.",
        "If search results are limited, clearly state the limitations of available information."
    ],
    mcp_servers=[
        MCPServerConfig(
            name="brave_search",
            transport="stdio", 
            command="npx -y @modelcontextprotocol/server-brave-search",
            enabled=True,
            description="Web search capabilities using Brave Search API",
            env={"BRAVE_API_KEY": ""}  # Requires user configuration
        )
    ],
    tags=["web", "search", "research", "current-info", "sources"],
    icon="./front/src/renderer/src/assets/agents/web-search.png",
    example_prompts=[
        "What's the latest news about renewable energy developments?",
        "Search for current information about cryptocurrency trends",
        "Find recent studies on remote work productivity", 
        "What are the latest AI breakthroughs this year?",
        "Search for current web development best practices"
    ],
    welcome_message="I'm your web search assistant! I can help you find current, well-sourced information on any topic. I'll search the web and provide you with up-to-date answers. What would you like to research today?"
)
```

## Troubleshooting

### Common Issues

**Agent not appearing**: Check that the agent template is properly added to `_get_prebuilt_agent_templates()`

**Icon not loading**: Verify the icon path is correct and the file exists

**MCP server errors**: Ensure the MCP server command is correct and dependencies are available

**Environment variables**: Make sure required env vars are documented and the `env` dict includes empty placeholders

### Debug Commands

```bash
# Test pre-built agent creation
python test_prebuilt_agents.py

# Run full MCP integration test
python test_mcp_integration.py

# Check agent database
python -c "from api.mcp_agents.service import MCPAgentService; import asyncio; service = MCPAgentService(); print(asyncio.run(service.get_prebuilt_agents()))"
```

## Contributing

When contributing new pre-built agents:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-agent-name`
3. Add your agent following this guide
4. Add tests for your agent
5. Update documentation if needed
6. Submit a pull request with:
   - Clear description of the agent's purpose
   - Screenshots of the agent in action
   - Test results
   - Any special configuration requirements

---

*This guide ensures consistent, high-quality pre-built agents that provide immediate value to users while showcasing the power of MCP integration.* 