"""
Enhanced MCP Agent Service

Service layer for managing agents using Ollama models with latest Agno MCP features.
Supports multiple transport types, MultiMCPTools, and includes sample agents.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import uuid
from pathlib import Path
import sqlite3

from api.ollama_client import OllamaPackage, OllamaMCPAgent
from .models import (
    MCPAgent, MCPServerConfig, 
    CreateMCPAgentRequest, UpdateMCPAgentRequest,
    MCPServerTemplate, AgentTemplate
)
from api.logger import app_logger

logger = logging.getLogger("mcp_agent_service")


class MCPAgentService:
    """Enhanced service for managing agents using Ollama models with latest Agno MCP features"""
    
    def __init__(self, db_path: str = "api/mcp_agents.db"):
        self.db_path = db_path
        self.active_agents: Dict[str, OllamaMCPAgent] = {}
        self._init_database()
        
        # Remove automatic sample creation - handle via API endpoints instead
        # if self._is_first_run():
        #     asyncio.create_task(self._create_sample_agents())
    
    def _init_database(self):
        """Initialize the SQLite database with enhanced schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Drop the old table if it exists (for clean upgrade)
        # cursor.execute("DROP TABLE IF EXISTS mcp_agents")
        
        # Check if table exists and get its columns
        cursor.execute("PRAGMA table_info(mcp_agents)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Create the enhanced table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                instructions TEXT,
                model_name TEXT NOT NULL,
                model_provider TEXT NOT NULL DEFAULT 'ollama',
                mcp_servers TEXT,
                tags TEXT,
                category TEXT,
                icon TEXT,
                example_prompts TEXT,
                welcome_message TEXT,
                markdown BOOLEAN DEFAULT 1,
                show_tool_calls BOOLEAN DEFAULT 1,
                add_datetime_to_instructions BOOLEAN DEFAULT 0,
                version TEXT DEFAULT '1.0.0',
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create service metadata table for tracking initialization state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Add missing columns if they don't exist
        new_columns = {
            'category': 'TEXT',
            'welcome_message': 'TEXT',
            'markdown': 'BOOLEAN DEFAULT 1',
            'show_tool_calls': 'BOOLEAN DEFAULT 1',
            'add_datetime_to_instructions': 'BOOLEAN DEFAULT 0',
            'version': 'TEXT DEFAULT "1.0.0"',
            'is_active': 'BOOLEAN DEFAULT 1',
            'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE mcp_agents ADD COLUMN {column_name} {column_type}")
                    logger.info(f"Added column {column_name} to mcp_agents table")
                except sqlite3.OperationalError as e:
                    # Column might already exist in some cases
                    logger.debug(f"Column {column_name} may already exist: {e}")
        
        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcp_agents_category ON mcp_agents(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcp_agents_is_active ON mcp_agents(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mcp_agents_created_at ON mcp_agents(created_at)")
        
        conn.commit()
        conn.close()
        logger.info("Enhanced agents database initialized")
    
    def _is_first_run(self) -> bool:
        """Check if this is the first run (no sample agents created yet)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT value FROM service_metadata WHERE key = 'sample_agents_created'")
        result = cursor.fetchone()
        conn.close()
        
        return result is None
    
    def _mark_sample_agents_created(self):
        """Mark that sample agents have been created"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR REPLACE INTO service_metadata (key, value) VALUES (?, ?)",
            ("sample_agents_created", "true")
        )
        
        conn.commit()
        conn.close()
    
    async def _create_sample_agents(self):
        """Create sample MCP agents with various useful configurations"""
        try:
            sample_agents = self._get_sample_agent_templates()
            
            for template in sample_agents:
                await self.create_agent(CreateMCPAgentRequest(
                    name=template.name,
                    description=template.description,
                    instructions=template.instructions,
                    mcp_servers=template.mcp_servers,
                    tags=template.tags,
                    category=template.category,
                    example_prompts=template.example_prompts,
                    icon=template.icon,
                    welcome_message=template.welcome_message
                ))
            
            self._mark_sample_agents_created()
            app_logger.info(f"Created {len(sample_agents)} sample MCP agents")
            
        except Exception as e:
            app_logger.error(f"Error creating sample agents: {str(e)}")
    
    def _get_sample_agent_templates(self) -> List[AgentTemplate]:
        """Get predefined sample agent templates"""
        return [
            # Filesystem Explorer Agent
            AgentTemplate(
                name="📁 Filesystem Explorer",
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
                        description="Access to local filesystem for reading and exploring files"
                    )
                ],
                tags=["filesystem", "development", "analysis"],
                example_prompts=[
                    "What files are in the current directory?",
                    "Show me the project structure",
                    "Find all Python files in this project",
                    "What's in the README file?",
                    "Analyze the project's dependencies"
                ],
                icon="📁",
                welcome_message="I'm your filesystem explorer! I can help you navigate, analyze, and understand your project structure and files. What would you like to explore today?"
            ),
            
            # GitHub Assistant Agent
            AgentTemplate(
                name="🐙 GitHub Assistant",
                description="Manage GitHub repositories, issues, and pull requests efficiently",
                category="development",
                instructions=[
                    "You are a GitHub assistant that helps with repository management.",
                    "Help users explore repositories, manage issues, and review pull requests.",
                    "Use headings to organize your responses.",
                    "Be concise and focus on relevant information.",
                    "Always provide actionable insights and suggestions."
                ],
                mcp_servers=[
                    MCPServerConfig(
                        name="github",
                        transport="stdio",
                        command="npx -y @modelcontextprotocol/server-github",
                        description="GitHub API integration for repository management",
                        env={"GITHUB_TOKEN": ""}  # Will need to be configured by user
                    )
                ],
                tags=["github", "git", "development", "collaboration"],
                example_prompts=[
                    "Show me recent issues in this repository",
                    "What pull requests need review?",
                    "Find issues labeled as 'bug'",
                    "Show repository statistics",
                    "List recent commits"
                ],
                icon="🐙",
                welcome_message="I'm your GitHub assistant! I can help you manage repositories, track issues, review pull requests, and analyze your GitHub workflow. Note: You'll need to configure your GitHub token for full functionality."
            ),
            
            # Search & Research Agent
            AgentTemplate(
                name="🔍 Research Assistant",
                description="Search the web and gather comprehensive research on any topic",
                category="research",
                instructions=[
                    "You are a research assistant that helps users find and analyze information.",
                    "Use Brave search to find current and relevant information.",
                    "Always verify information from multiple sources when possible.",
                    "Provide well-structured summaries with clear headings.",
                    "Include relevant links and sources in your responses.",
                    "Be objective and highlight any limitations in the available information."
                ],
                mcp_servers=[
                    MCPServerConfig(
                        name="brave_search",
                        transport="stdio",
                        command="npx -y @modelcontextprotocol/server-brave-search",
                        description="Web search capabilities using Brave Search API",
                        env={"BRAVE_API_KEY": ""}  # Will need to be configured by user
                    )
                ],
                tags=["search", "research", "web", "information"],
                example_prompts=[
                    "What's the latest news about AI developments?",
                    "Research the benefits of renewable energy",
                    "Find information about Python best practices",
                    "What are the current trends in web development?",
                    "Search for recent scientific studies on climate change"
                ],
                icon="🔍",
                welcome_message="I'm your research assistant! I can search the web and help you gather comprehensive information on any topic. Note: You'll need to configure your Brave API key for search functionality."
            ),
            
            # Travel Planning Agent
            AgentTemplate(
                name="✈️ Travel Planner",
                description="Plan trips with accommodation search and location insights",
                category="productivity",
                instructions=[
                    "You are a travel planning assistant that helps users plan their trips.",
                    "Use Airbnb search to find accommodations and Google Maps for location information.",
                    "Provide comprehensive travel advice including accommodation options.",
                    "Consider factors like location, price, amenities, and user preferences.",
                    "Offer practical travel tips and local insights when available.",
                    "Structure your responses with clear sections for different aspects of travel planning."
                ],
                mcp_servers=[
                    MCPServerConfig(
                        name="airbnb",
                        transport="stdio",
                        command="npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
                        description="Search Airbnb listings for accommodations"
                    ),
                    MCPServerConfig(
                        name="google_maps",
                        transport="stdio",
                        command="npx -y @modelcontextprotocol/server-google-maps",
                        description="Location information and mapping services",
                        env={"GOOGLE_MAPS_API_KEY": ""}  # Will need to be configured by user
                    )
                ],
                tags=["travel", "planning", "accommodation", "maps"],
                example_prompts=[
                    "Find Airbnb listings in Tokyo for 2 people for 5 nights",
                    "Plan a weekend trip to San Francisco",
                    "What are the best areas to stay in Barcelona?",
                    "Find pet-friendly accommodations in New York",
                    "Compare accommodation options in London vs Paris"
                ],
                icon="✈️",
                welcome_message="I'm your travel planning assistant! I can help you find accommodations, explore destinations, and plan amazing trips. Note: Google Maps integration requires an API key for full functionality."
            ),
            
            # Analytical Thinking Agent
            AgentTemplate(
                name="🧠 Analytical Thinker",
                description="Solve complex problems with structured thinking and financial analysis",
                category="analysis",
                instructions=[
                    "You are an analytical assistant that helps users solve complex problems.",
                    "Use the sequential thinking tool to break down complex problems step by step.",
                    "Before taking any action, use the think tool as a scratchpad to organize your thoughts.",
                    "Provide structured analysis with clear reasoning.",
                    "When analyzing financial topics, use YFinance tools for current market data.",
                    "Always verify your reasoning and double-check important conclusions.",
                    "Use tables and clear formatting to present complex information."
                ],
                mcp_servers=[
                    MCPServerConfig(
                        name="sequential_thinking",
                        transport="stdio",
                        command="npx -y @modelcontextprotocol/server-sequential-thinking",
                        description="Structured thinking and problem-solving capabilities"
                    )
                ],
                tags=["analysis", "thinking", "problem-solving", "finance"],
                example_prompts=[
                    "Analyze the pros and cons of remote work",
                    "Compare different investment strategies",
                    "Break down this complex problem step by step",
                    "Help me make a data-driven decision",
                    "Analyze market trends for tech companies"
                ],
                icon="🧠",
                welcome_message="I'm your analytical thinking assistant! I can help you solve complex problems, analyze data, and make structured decisions using systematic thinking approaches."
            ),
            
            # Git Assistant Agent
            AgentTemplate(
                name="🌿 Git Assistant",
                description="Manage Git repositories and version control workflows",
                category="development",
                instructions=[
                    "You are a Git assistant that helps with version control workflows.",
                    "Help users understand repository status, manage branches, and review changes.",
                    "Provide clear explanations of Git operations and best practices.",
                    "Suggest appropriate Git workflows based on the project context.",
                    "Always explain the implications of Git operations before suggesting them.",
                    "Format responses with clear sections and code examples when helpful."
                ],
                mcp_servers=[
                    MCPServerConfig(
                        name="git",
                        transport="stdio",
                        command="uvx mcp-server-git",
                        description="Git repository management and version control operations"
                    )
                ],
                tags=["git", "version-control", "development", "collaboration"],
                example_prompts=[
                    "What's the current status of this repository?",
                    "Show me recent commits",
                    "What files have been changed?",
                    "Help me understand the branch structure",
                    "What are the best practices for this workflow?"
                ],
                icon="🌿",
                welcome_message="I'm your Git assistant! I can help you manage repositories, understand version control workflows, and follow Git best practices."
            )
        ]
    
    async def create_agent(self, request: CreateMCPAgentRequest) -> MCPAgent:
        """Create a new agent using enhanced Ollama MCP capabilities"""
        agent_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Store in database with enhanced fields
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO mcp_agents 
                (id, name, description, instructions, model_name, model_provider, mcp_servers, 
                 tags, category, icon, example_prompts, welcome_message, markdown, show_tool_calls,
                 add_datetime_to_instructions, version, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                request.name,
                request.description or "",
                json.dumps(request.instructions),
                request.model_name,
                "ollama",  # Force ollama provider
                json.dumps([server.dict() for server in (request.mcp_servers or [])]),
                json.dumps(request.tags or []),
                request.category,
                request.icon or "",
                json.dumps(request.example_prompts or []),
                request.welcome_message,
                request.markdown,
                request.show_tool_calls,
                request.add_datetime_to_instructions,
                "1.0.0",
                True
            ))
            
            conn.commit()
            conn.close()
            
            # Create and return the agent model
            agent = MCPAgent(
                id=agent_id,
                name=request.name,
                description=request.description or "",
                instructions=request.instructions,
                model_name=request.model_name,
                model_provider="ollama",
                mcp_servers=request.mcp_servers or [],
                tags=request.tags or [],
                category=request.category,
                icon=request.icon or "",
                example_prompts=request.example_prompts or [],
                welcome_message=request.welcome_message,
                markdown=request.markdown,
                show_tool_calls=request.show_tool_calls,
                add_datetime_to_instructions=request.add_datetime_to_instructions
            )
            
            app_logger.info(f"Created enhanced MCP agent: {agent_id}")
            return agent
            
        except Exception as e:
            app_logger.error(f"Error creating agent: {str(e)}")
            raise
    
    async def get_agent(self, agent_id: str) -> Optional[MCPAgent]:
        """Get an agent by ID with enhanced fields"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM mcp_agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return MCPAgent(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    instructions=json.loads(row[3]),
                    model_name=row[4],
                    model_provider=row[5],
                    mcp_servers=[MCPServerConfig(**server) for server in json.loads(row[6])],
                    tags=json.loads(row[7]) if row[7] else [],
                    category=row[8],
                    icon=row[9] or "",
                    example_prompts=json.loads(row[10]) if row[10] else [],
                    welcome_message=row[11],
                    markdown=bool(row[12]) if row[12] is not None else True,
                    show_tool_calls=bool(row[13]) if row[13] is not None else True,
                    add_datetime_to_instructions=bool(row[14]) if row[14] is not None else False,
                    version=row[15] or "1.0.0",
                    is_active=bool(row[16]) if row[16] is not None else True,
                    created_at=row[17],
                    updated_at=row[18]
                )
            return None
            
        except Exception as e:
            app_logger.error(f"Error getting agent {agent_id}: {str(e)}")
            return None
    
    async def get_all_agents(self) -> List[MCPAgent]:
        """Get all agents with enhanced data and statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM mcp_agents WHERE is_active = 1 ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            agents = []
            for row in rows:
                agents.append(MCPAgent(
                    id=row[0],
                    name=row[1],
                    description=row[2],
                    instructions=json.loads(row[3]),
                    model_name=row[4],
                    model_provider=row[5],
                    mcp_servers=[MCPServerConfig(**server) for server in json.loads(row[6])],
                    tags=json.loads(row[7]) if row[7] else [],
                    category=row[8],
                    icon=row[9] or "",
                    example_prompts=json.loads(row[10]) if row[10] else [],
                    welcome_message=row[11],
                    markdown=bool(row[12]) if row[12] is not None else True,
                    show_tool_calls=bool(row[13]) if row[13] is not None else True,
                    add_datetime_to_instructions=bool(row[14]) if row[14] is not None else False,
                    version=row[15] or "1.0.0",
                    is_active=bool(row[16]) if row[16] is not None else True,
                    created_at=row[17],
                    updated_at=row[18]
                ))
            
            return agents
            
        except Exception as e:
            app_logger.error(f"Error getting all agents: {str(e)}")
            return []
    
    async def update_agent(self, agent_id: str, updates: Dict[str, Any]) -> Optional[MCPAgent]:
        """Update an agent with enhanced fields support"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build update query dynamically
            update_fields = []
            values = []
            
            for field, value in updates.items():
                if field in ['name', 'description', 'model_name', 'model_provider', 'category', 'icon', 'welcome_message', 'version']:
                    update_fields.append(f"{field} = ?")
                    values.append(value)
                elif field in ['instructions', 'mcp_servers', 'tags', 'example_prompts']:
                    update_fields.append(f"{field} = ?")
                    values.append(json.dumps(value))
                elif field in ['markdown', 'show_tool_calls', 'add_datetime_to_instructions', 'is_active']:
                    update_fields.append(f"{field} = ?")
                    values.append(bool(value))
            
            if update_fields:
                update_fields.append("updated_at = ?")
                values.append(datetime.now().isoformat())
                values.append(agent_id)
                
                query = f"UPDATE mcp_agents SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(query, values)
                
                if cursor.rowcount > 0:
                    conn.commit()
                    conn.close()
                    
                    # Clean up active agent if it exists (will be recreated on next use)
                    if agent_id in self.active_agents:
                        await self._cleanup_agent(agent_id)
                    
                    return await self.get_agent(agent_id)
            
            conn.close()
            return None
            
        except Exception as e:
            app_logger.error(f"Error updating agent {agent_id}: {str(e)}")
            return None
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        try:
            # Clean up any active agent
            if agent_id in self.active_agents:
                await self._cleanup_agent(agent_id)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("UPDATE mcp_agents SET is_active = 0 WHERE id = ?", (agent_id,))
            deleted = cursor.rowcount > 0
            
            conn.commit()
            conn.close()
            
            if deleted:
                app_logger.info(f"Soft deleted agent: {agent_id}")
            
            return deleted
            
        except Exception as e:
            app_logger.error(f"Error deleting agent {agent_id}: {str(e)}")
            return False
    
    async def start_agent(self, agent_id: str) -> Optional[OllamaMCPAgent]:
        """Start an MCP agent using enhanced OllamaPackage with MultiMCPTools support"""
        try:
            # Check if agent is already active
            if agent_id in self.active_agents:
                return self.active_agents[agent_id]
            
            agent_config = await self.get_agent(agent_id)
            if not agent_config:
                return None
            
            # Prepare MCP configuration for MultiMCPTools
            mcp_commands = []
            mcp_urls = []
            mcp_env = {}
            
            # Collect enabled servers by transport type
            for server in agent_config.mcp_servers:
                if not server.enabled:
                    continue
                    
                # Add environment variables
                if server.env:
                    mcp_env.update(server.env)
                
                if server.transport == "stdio" and server.command:
                    command = server.command
                    if server.args:
                        command += " " + " ".join(server.args)
                    mcp_commands.append(command)
                elif server.transport in ["sse", "streamable-http"] and server.url:
                    mcp_urls.append(server.url)
            
            # Create agent with enhanced configuration
            agent_instance = await OllamaPackage.create_mcp_agent(
                model_name=agent_config.model_name,
                system_message=None,  # Will use instructions from config
                session_id=agent_id,
                verbose=True,
                use_config_system_prompt=False,  # Use our custom instructions
                mcp_commands=mcp_commands if mcp_commands else None,
                mcp_urls=mcp_urls if mcp_urls else None,
                mcp_env=mcp_env if mcp_env else None,
            )
            
            # Apply agent-specific configuration
            if agent_instance and agent_instance.agent:
                agent_instance.agent.description = agent_config.description
                agent_instance.agent.instructions = agent_config.instructions
                agent_instance.agent.markdown = agent_config.markdown
                agent_instance.agent.show_tool_calls = agent_config.show_tool_calls
                agent_instance.agent.add_datetime_to_instructions = agent_config.add_datetime_to_instructions
            
            # Store the active agent
            self.active_agents[agent_id] = agent_instance
            
            app_logger.info(f"Started enhanced MCP agent: {agent_id} with {len(mcp_commands)} commands and {len(mcp_urls)} URLs")
            return agent_instance
            
        except Exception as e:
            app_logger.error(f"Error starting agent {agent_id}: {str(e)}")
            return None
    
    async def chat_with_agent(self, agent_id: str, message: str) -> str:
        """Chat with an agent, starting it if necessary"""
        try:
            agent = await self.start_agent(agent_id)
            if not agent:
                return "Error: Could not start the agent. Please check the agent configuration."
            
            response = await agent.chat(message)
            return response
            
        except Exception as e:
            app_logger.error(f"Error chatting with agent {agent_id}: {str(e)}")
            return f"Error: {str(e)}"
    
    async def stream_chat_with_agent(self, agent_id: str, message: str):
        """Stream chat with an agent"""
        try:
            agent = await self.start_agent(agent_id)
            if not agent:
                yield f"data: {json.dumps({'error': 'Could not start the agent'})}\n\n"
                return
            
            # Use the agent's streaming capabilities
            response_buffer = []
            try:
                if hasattr(agent.agent, 'run') and callable(agent.agent.run):
                    # Try Agno's native streaming
                    run_response = agent.agent.run(message, stream=True)
                    
                    for chunk in run_response:
                        if hasattr(chunk, 'content') and chunk.content:
                            content = chunk.content
                            response_buffer.append(content)
                            
                            # Stream content word by word for better UX
                            import re
                            parts = re.findall(r'\S+|\s+', content)
                            for part in parts:
                                yield f"data: {json.dumps({'text': part})}\n\n"
                                await asyncio.sleep(0.02)
                else:
                    # Fallback to regular chat
                    response = await agent.chat(message)
                    response_buffer.append(response)
                    
                    # Stream word by word
                    import re
                    parts = re.findall(r'\S+|\s+', response)
                    for part in parts:
                        yield f"data: {json.dumps({'text': part})}\n\n"
                        await asyncio.sleep(0.03)
                
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as stream_error:
                app_logger.error(f"Streaming error for agent {agent_id}: {stream_error}")
                yield f"data: {json.dumps({'error': str(stream_error)})}\n\n"
            
        except Exception as e:
            app_logger.error(f"Error streaming with agent {agent_id}: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    async def _cleanup_agent(self, agent_id: str):
        """Clean up an active agent with proper resource management"""
        try:
            if agent_id in self.active_agents:
                agent = self.active_agents[agent_id]
                if agent:
                    await agent.cleanup()
                del self.active_agents[agent_id]
                app_logger.info(f"Cleaned up enhanced agent: {agent_id}")
        except Exception as e:
            app_logger.error(f"Error cleaning up agent {agent_id}: {str(e)}")
    
    async def cleanup_all_agents(self):
        """Clean up all active agents"""
        try:
            for agent_id in list(self.active_agents.keys()):
                await self._cleanup_agent(agent_id)
            app_logger.info("All enhanced MCP agents cleaned up")
        except Exception as e:
            app_logger.error(f"Error cleaning up all agents: {str(e)}")
    
    async def get_available_models(self) -> List[str]:
        """Get available Ollama models"""
        try:
            models = await OllamaPackage.get_available_models()
            return models
        except Exception as e:
            app_logger.error(f"Error getting available models: {str(e)}")
            return []
    
    async def get_agent_categories(self) -> List[str]:
        """Get all unique agent categories"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT category FROM mcp_agents WHERE category IS NOT NULL AND is_active = 1")
            categories = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return sorted(categories)
        except Exception as e:
            app_logger.error(f"Error getting agent categories: {str(e)}")
            return []
    
    async def get_mcp_server_templates(self) -> List[MCPServerTemplate]:
        """Get predefined MCP server templates for easy configuration"""
        return [
            MCPServerTemplate(
                name="Filesystem",
                description="Access and explore local filesystem",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-filesystem .",
                category="development",
                tags=["filesystem", "files", "development"],
                example_instructions=["Navigate the filesystem to answer questions", "Provide clear context about files you examine"],
                icon="📁"
            ),
            MCPServerTemplate(
                name="GitHub",
                description="GitHub repository management",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-github",
                env_vars=["GITHUB_TOKEN"],
                category="development",
                tags=["github", "git", "repositories"],
                example_instructions=["Help users explore repositories", "Manage issues and pull requests"],
                icon="🐙"
            ),
            MCPServerTemplate(
                name="Brave Search",
                description="Web search using Brave Search API",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-brave-search",
                env_vars=["BRAVE_API_KEY"],
                category="research",
                tags=["search", "web", "research"],
                example_instructions=["Search the web for current information", "Provide well-structured summaries"],
                icon="🔍"
            ),
            MCPServerTemplate(
                name="Airbnb",
                description="Search Airbnb listings",
                transport="stdio",
                command="npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
                category="travel",
                tags=["airbnb", "travel", "accommodation"],
                example_instructions=["Help users find accommodations", "Consider location, price, and amenities"],
                icon="🏠"
            ),
            MCPServerTemplate(
                name="Google Maps",
                description="Location and mapping services",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-google-maps",
                env_vars=["GOOGLE_MAPS_API_KEY"],
                category="travel",
                tags=["maps", "location", "travel"],
                example_instructions=["Provide location information", "Help with travel planning"],
                icon="🗺️"
            ),
            MCPServerTemplate(
                name="Sequential Thinking",
                description="Structured problem-solving capabilities",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-sequential-thinking",
                category="analysis",
                tags=["thinking", "analysis", "problem-solving"],
                example_instructions=["Use the think tool as a scratchpad", "Break down complex problems step by step"],
                icon="🧠"
            ),
            MCPServerTemplate(
                name="Git",
                description="Git repository operations",
                transport="stdio",
                command="uvx mcp-server-git",
                category="development",
                tags=["git", "version-control", "development"],
                example_instructions=["Help with Git workflows", "Explain Git operations clearly"],
                icon="🌿"
            )
        ]

    async def create_sample_agents(self) -> List[MCPAgent]:
        """Create and initialize sample MCP agents using the best templates."""
        sample_agents = []
        
        # Get server templates for creating sample agents
        templates = await self.get_mcp_server_templates()
        
        # Select popular/useful templates for samples
        sample_templates = [
            next((t for t in templates if t.name == "Filesystem"), None),
            next((t for t in templates if t.name == "GitHub"), None),
            next((t for t in templates if t.name == "Web Search"), None),
            next((t for t in templates if t.name == "Git"), None),
        ]
        
        for template in sample_templates:
            if template is None:
                continue
            
            try:
                # Create agent from template
                agent_request = CreateMCPAgentRequest(
                    name=f"Sample {template.name} Agent",
                    description=f"A pre-configured {template.name.lower()} agent ready to use. {template.description}",
                    instructions=[
                        "You are a helpful AI assistant.",
                        f"You have access to {template.name.lower()} tools.",
                        "Use your tools when needed to help users effectively.",
                        "Always explain what you're doing when using tools."
                    ],
                    model_name="llama3.2",
                    model_provider="ollama",
                    mcp_servers=[{
                        "name": template.name.lower().replace(" ", "_"),
                        "transport": template.transport,
                        "command": template.command if template.command else None,
                        "url": template.url if template.url else None,
                        "enabled": True,
                        "description": template.description,
                        "env": {var: "" for var in template.env_vars} if template.env_vars else {}
                    }],
                    tags=template.tags + ["sample", "ready-to-use"],
                    category=template.category,
                    icon=template.icon or "🤖",
                    example_prompts=[
                        f"Help me use {template.name.lower()} effectively",
                        f"What can you do with {template.name.lower()}?",
                        f"Show me an example of {template.name.lower()} usage"
                    ],
                    welcome_message=f"I'm your {template.name} assistant! I can help you with {template.description.lower()}. What would you like to do?",
                    markdown=True,
                    show_tool_calls=True,
                    add_datetime_to_instructions=False
                )
                
                # Check if agent with this name already exists
                existing_agents = await self.get_all_agents()
                if any(agent.name == agent_request.name for agent in existing_agents):
                    continue
                
                agent = await self.create_agent(agent_request)
                if agent:
                    sample_agents.append(agent)
                    logger.info(f"Created sample agent: {agent.name}")
                    
            except Exception as e:
                logger.error(f"Error creating sample agent for {template.name}: {str(e)}")
        
        return sample_agents

    async def initialize_sample_agents_if_empty(self) -> bool:
        """Initialize sample agents if no agents exist."""
        try:
            agents = await self.get_all_agents()
            if len(agents) == 0:
                logger.info("No agents found, creating sample agents...")
                sample_agents = await self.create_sample_agents()
                logger.info(f"Created {len(sample_agents)} sample agents")
                return True
            return False
        except Exception as e:
            logger.error(f"Error initializing sample agents: {str(e)}")
            return False

if __name__ == "__main__":
    import asyncio
    
    async def main():
        service = MCPAgentService()
        
        # Initialize sample agents if none exist
        await service.initialize_sample_agents_if_empty()
        
        # List all agents
        agents = await service.get_all_agents()
        print(f"\nFound {len(agents)} MCP agents:")
        for agent in agents:
            print(f"- {agent.name}: {agent.description}")
            print(f"  Category: {agent.category}, Tags: {agent.tags}")
            print(f"  MCP Servers: {len(agent.mcp_servers)}")
            if agent.mcp_servers:
                for server in agent.mcp_servers:
                    print(f"    - {server.name} ({server.transport})")
            print()
    
    asyncio.run(main()) 