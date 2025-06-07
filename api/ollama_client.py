import sys
import os
import inspect
import asyncio
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

# Determine the absolute path of the current script
try:
    current_file_path = os.path.abspath(inspect.getfile(inspect.currentframe()))
except TypeError:
    current_file_path = os.path.abspath(__file__)

# Directory containing the script (api directory)
script_dir = os.path.dirname(current_file_path)
# Project root directory (parent of the script directory)
project_root = os.path.dirname(script_dir)

# If the project root isn't already in sys.path, add it.
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Core Agno framework imports - using basic features only
from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.tools import tool

# Import MCP support from Agno
try:
    from agno.tools.mcp import MCPTools, MultiMCPTools
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

from dotenv import load_dotenv

# Import the logger
from api.logger import app_logger
from api.config_io import read_ollama_config, get_active_system_prompt

# Import embedding models scraper function
from api.scrape_ollama import fetch_embedding_models

load_dotenv()  # load environment variables from .env


class OllamaMCPAgent:
    """
    Advanced Ollama Agent with MCP (Model Context Protocol) support using Agno framework.
    Supports connecting to multiple MCP servers for external tool integration.
    """

    def __init__(
        self,
        model_name: str = "llama3.2",
        vision_model_name: str = "granite3.2-vision",
        system_message: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        verbose: bool = False,
        user_id: str = "default",
        session_id: Optional[str] = None,
        use_config_system_prompt: bool = True,
        mcp_commands: Optional[List[str]] = None,
        mcp_urls: Optional[List[str]] = None,
        mcp_env: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the Ollama MCP Agent with support for external MCP servers.

        Args:
            model_name: Name of the Ollama model to use
            vision_model_name: Name of the Ollama vision model to use
            system_message: Optional system message to override config (legacy support)
            base_url: Base URL for the Ollama API (default: http://localhost:11434)
            temperature: Temperature parameter for generation
            top_p: Top-p parameter for generation
            verbose: Whether to output verbose logs
            user_id: User ID for the agent
            session_id: Session ID for conversations
            use_config_system_prompt: Whether to use configured system prompts
            mcp_commands: List of MCP server commands to connect to (e.g., ["uvx mcp-server-git"])
            mcp_urls: List of MCP server URLs to connect to (for remote servers)
            mcp_env: Environment variables for MCP servers
        """
        self.model_name = model_name
        self.vision_model_name = vision_model_name
        self.system_message = system_message
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = temperature
        self.top_p = top_p
        self.verbose = verbose
        self.user_id = user_id
        self.session_id = session_id
        self.use_config_system_prompt = use_config_system_prompt
        self.mcp_commands = mcp_commands or []
        self.mcp_urls = mcp_urls or []
        self.mcp_env = mcp_env or {}

        # Ensure the base URL doesn't include /v1 (Agno handles this)
        if self.base_url.endswith('/v1'):
            self.base_url = self.base_url.rstrip('/v1')

        # Initialize Ollama model for chat
        self.model = OpenAILike(
            id=self.model_name,
            api_key="ollama",  # Required but unused by Ollama
            base_url=f"{self.base_url}/v1",
            temperature=self.temperature,
            top_p=self.top_p,
        )

        # Initialize vision model if different
        self.vision_model = None
        if self.vision_model_name and self.vision_model_name != self.model_name:
            self.vision_model = OpenAILike(
                id=self.vision_model_name,
                api_key="ollama",
                base_url=f"{self.base_url}/v1",
                temperature=self.temperature,
                top_p=self.top_p,
            )

        # MCP tools context manager
        self.mcp_tools = None
        self.agent = None

        if self.verbose:
            app_logger.info(f"Initialized Ollama MCP Agent with model: {self.model_name}")
            app_logger.info(f"Base URL: {self.base_url}")
            if self.mcp_commands:
                app_logger.info(f"MCP commands configured: {self.mcp_commands}")
            if self.mcp_urls:
                app_logger.info(f"MCP URLs configured: {self.mcp_urls}")

    async def initialize_mcp(self):
        """Initialize MCP connections and create the agent."""
        if not MCP_AVAILABLE:
            app_logger.warning("MCP support not available. Install with: pip install agno[mcp]")
            return await self._create_basic_agent()

        tools = []

        # Initialize MCP tools if any MCP servers are configured
        if self.mcp_commands or self.mcp_urls:
            try:
                if len(self.mcp_commands) + len(self.mcp_urls) > 1:
                    # Use MultiMCPTools for multiple servers
                    self.mcp_tools = await MultiMCPTools(
                        commands=self.mcp_commands if self.mcp_commands else None,
                        urls=self.mcp_urls if self.mcp_urls else None,
                        env=self.mcp_env if self.mcp_env else None,
                    ).__aenter__()
                    tools.append(self.mcp_tools)
                    
                    if self.verbose:
                        app_logger.info(f"Connected to {len(self.mcp_commands) + len(self.mcp_urls)} MCP servers")
                        
                elif self.mcp_commands:
                    # Single command server
                    self.mcp_tools = await MCPTools(
                        command=self.mcp_commands[0],
                        env=self.mcp_env if self.mcp_env else None,
                    ).__aenter__()
                    tools.append(self.mcp_tools)
                    
                    if self.verbose:
                        app_logger.info(f"Connected to MCP server: {self.mcp_commands[0]}")
                        
                elif self.mcp_urls:
                    # Single URL server
                    self.mcp_tools = await MCPTools(
                        url=self.mcp_urls[0],
                        env=self.mcp_env if self.mcp_env else None,
                    ).__aenter__()
                    tools.append(self.mcp_tools)
                    
                    if self.verbose:
                        app_logger.info(f"Connected to MCP server: {self.mcp_urls[0]}")

            except Exception as e:
                app_logger.error(f"Failed to initialize MCP tools: {e}")
                # Fall back to basic agent without MCP
                return await self._create_basic_agent()

        # Add default tools
        tools.extend([get_current_time, calculate])

        # Get system prompt configuration
        prompt_config = self._get_system_prompt_config()

        # Initialize the Agno agent with MCP tools
        self.agent = Agent(
            model=self.model,
            user_id=self.user_id,
            session_id=self.session_id,
            description=prompt_config.get("description", ""),
            instructions=prompt_config.get("instructions", []),
            additional_context=prompt_config.get("additional_context", ""),
            expected_output=prompt_config.get("expected_output", ""),
            markdown=prompt_config.get("markdown", True),
            add_datetime_to_instructions=prompt_config.get("add_datetime_to_instructions", False),
            show_tool_calls=self.verbose,
            debug_mode=self.verbose,
            tools=tools,
        )

        if self.verbose:
            app_logger.info(f"MCP Agent initialized with {len(tools)} tool sets")

        return self.agent

    async def _create_basic_agent(self):
        """Create a basic agent without MCP support (fallback)."""
        # Get system prompt configuration
        prompt_config = self._get_system_prompt_config()

        # Initialize the Agno agent with basic tools only
        self.agent = Agent(
            model=self.model,
            user_id=self.user_id,
            session_id=self.session_id,
            description=prompt_config.get("description", ""),
            instructions=prompt_config.get("instructions", []),
            additional_context=prompt_config.get("additional_context", ""),
            expected_output=prompt_config.get("expected_output", ""),
            markdown=prompt_config.get("markdown", True),
            add_datetime_to_instructions=prompt_config.get("add_datetime_to_instructions", False),
            show_tool_calls=self.verbose,
            debug_mode=self.verbose,
            tools=[get_current_time, calculate],
        )

        if self.verbose:
            app_logger.info("Basic agent initialized (no MCP support)")

        return self.agent

    def _get_system_prompt_config(self) -> Dict[str, Any]:
        """
        Get the system prompt configuration based on settings.
        
        Returns:
            Dict containing the prompt configuration for Agno Agent
        """
        if not self.use_config_system_prompt and self.system_message:
            # Legacy mode: use the provided system_message
            return {
                "description": "",
                "instructions": [self.system_message] if self.system_message else [],
                "additional_context": "",
                "expected_output": "",
                "markdown": True,
                "add_datetime_to_instructions": False,
                "name": "Custom"
            }
        
        # Get active system prompt from configuration
        try:
            active_prompt = get_active_system_prompt()
            if active_prompt:
                return active_prompt
        except Exception as e:
            app_logger.warning(f"Failed to load system prompt config: {e}")
        
        # Fallback to default configuration
        return {
            "description": "You are a helpful AI assistant with access to external tools and services",
            "instructions": [
                "Always be friendly and informative.",
                "Use available tools to provide accurate and up-to-date information.",
                "When using MCP tools, explain what you're doing to help the user understand.",
                "If you're unsure about something, say so."
            ],
            "additional_context": "",
            "expected_output": "",
            "markdown": True,
            "add_datetime_to_instructions": False,
            "name": "Default MCP Fallback"
        }

    def update_system_prompt(self, prompt_config: Optional[Dict[str, Any]] = None):
        """
        Update the agent's system prompt configuration.
        
        Args:
            prompt_config: Optional specific prompt config, otherwise uses active config
        """
        if not self.agent:
            app_logger.warning("Agent not initialized, cannot update system prompt")
            return

        if prompt_config is None:
            prompt_config = self._get_system_prompt_config()
        
        # Update agent configuration
        self.agent.description = prompt_config.get("description", "")
        self.agent.instructions = prompt_config.get("instructions", [])
        self.agent.additional_context = prompt_config.get("additional_context", "")
        self.agent.expected_output = prompt_config.get("expected_output", "")
        self.agent.markdown = prompt_config.get("markdown", True)
        self.agent.add_datetime_to_instructions = prompt_config.get("add_datetime_to_instructions", False)
        
        if self.verbose:
            app_logger.info(f"Updated system prompt: {prompt_config.get('name', 'Custom')}")

    def get_current_prompt_info(self) -> Dict[str, Any]:
        """
        Get information about the current system prompt configuration.
        
        Returns:
            Dict containing current prompt information
        """
        if not self.agent:
            return {}

        return {
            "description": self.agent.description,
            "instructions": self.agent.instructions,
            "additional_context": self.agent.additional_context,
            "expected_output": self.agent.expected_output,
            "markdown": self.agent.markdown,
            "add_datetime_to_instructions": self.agent.add_datetime_to_instructions
        }

    def add_tools(self, tools: List[Any]):
        """Add tools to the agent."""
        if not self.agent:
            app_logger.warning("Agent not initialized, cannot add tools")
            return

        self.agent.tools.extend(tools)
        if self.verbose:
            app_logger.info(f"Added {len(tools)} tools to agent")

    async def add_file_context(self, file_path: Union[str, Path], file_name: str):
        """
        Add file context to the agent by reading the file and providing it as context.
        This is a simplified approach without vector databases.

        Args:
            file_path: Path to the uploaded file
            file_name: Original name of the file (used for metadata)
        """
        if not self.agent:
            app_logger.warning("Agent not initialized, cannot add file context")
            return

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found at {file_path}")

        app_logger.info(f"Processing file for context: {file_name} ({file_path.suffix})")

        try:
            text_content = ""
            if file_path.suffix == '.pdf':
                # Simple PDF reading without complex dependencies
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    text_content = "".join(page.extract_text() for page in reader.pages if page.extract_text())
                except ImportError:
                    raise ImportError("pypdf is required for PDF processing. Install with: pip install pypdf")
            elif file_path.suffix in ['.txt', '.md']:
                text_content = file_path.read_text(encoding='utf-8')
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")

            if not text_content.strip():
                raise ValueError(f"No text could be extracted from file: {file_name}")

            # Add the file content using Agno's additional_context feature
            context_text = f"Document '{file_name}':\n\n{text_content}\n\n"
            
            # Update the additional_context of the agent
            current_context = self.agent.additional_context or ""
            self.agent.additional_context = current_context + context_text

            app_logger.info(f"Successfully added context from {file_name} to agent.")

        except Exception as e:
            app_logger.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)
            raise

    async def chat(self, message: str, **kwargs) -> str:
        """
        Process a chat message using Agno agent.

        Args:
            message: The user's message
            **kwargs: Additional arguments passed to the agent

        Returns:
            The response from the agent
        """
        try:
            if not self.agent:
                await self.initialize_mcp()

            if not self.agent:
                raise RuntimeError("Agent initialization failed")

            # Use Agno's asynchronous response method
            response = await self.agent.arun(message, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            error_msg = f"Error processing message: {e}"
            app_logger.error(error_msg, exc_info=True)
            return error_msg

    def chat_sync(self, message: str, **kwargs) -> str:
        """
        Synchronous version of chat method.

        Args:
            message: The user's message
            **kwargs: Additional arguments passed to the agent

        Returns:
            The response from the agent
        """
        try:
            if not self.agent:
                # Run async initialization in sync context
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create new task if loop is already running
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.initialize_mcp())
                        future.result()
                else:
                    asyncio.run(self.initialize_mcp())

            if not self.agent:
                raise RuntimeError("Agent initialization failed")

            # Use Agno's synchronous response method
            response = self.agent.run(message, **kwargs)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            error_msg = f"Error processing message: {e}"
            app_logger.error(error_msg, exc_info=True)
            return error_msg

    def chat_stream(self, message: str, **kwargs):
        """
        Stream chat response using Agno agent.

        Args:
            message: The user's message
            **kwargs: Additional arguments passed to the agent
        """
        try:
            if not self.agent:
                # Initialize if needed
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self.initialize_mcp())
                        future.result()
                else:
                    asyncio.run(self.initialize_mcp())

            if not self.agent:
                raise RuntimeError("Agent initialization failed")

            # Use Agno's print_response with stream=True
            self.agent.print_response(message, stream=True, **kwargs)

        except Exception as e:
            error_msg = f"Error during chat streaming: {e}"
            app_logger.error(error_msg, exc_info=True)
            print(error_msg)

    async def chat_with_image(self, message: str, image_paths: List[Union[str, Path]], **kwargs) -> str:
        """
        Process a message with image context using vision model.

        Args:
            message: The user's text message
            image_paths: List of paths to images
            **kwargs: Additional arguments

        Returns:
            The response from the vision model
        """
        if not self.vision_model:
            return "No vision model specified for this agent."

        try:
            # For vision, we'll use the vision model directly
            from openai import AsyncOpenAI
            import base64

            client = AsyncOpenAI(
                base_url=f"{self.base_url}/v1",
                api_key="ollama",
            )

            # Prepare image content
            content = [{"type": "text", "text": message}]
            for image_path in image_paths:
                with open(image_path, "rb") as image_file:
                    image_data = base64.b64encode(image_file.read()).decode('utf-8')
                image_format = Path(image_path).suffix.lower().lstrip('.')
                if image_format == 'jpg':
                    image_format = 'jpeg'
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}
                })

            response = await client.chat.completions.create(
                model=self.vision_model_name,
                messages=[{"role": "user", "content": content}],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=300,
            )

            return response.choices[0].message.content

        except Exception as e:
            error_msg = f"Error during vision chat: {e}"
            app_logger.error(error_msg, exc_info=True)
            return error_msg

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history from the agent."""
        # Agno handles history internally
        return []

    def clear_history(self):
        """Clear the conversation history."""
        # Agno handles this through its internal mechanisms
        pass

    async def cleanup(self):
        """Clean up resources including MCP connections."""
        try:
            # Close MCP connections if they exist
            if self.mcp_tools:
                try:
                    await self.mcp_tools.__aexit__(None, None, None)
                except Exception as e:
                    app_logger.error(f"Error closing MCP connections: {e}")
                finally:
                    self.mcp_tools = None

            # Agno handles other cleanup automatically
            app_logger.info("MCP Agent cleanup completed")
        except Exception as e:
            app_logger.error(f"Error during cleanup: {e}")


# Legacy alias for backward compatibility
OllamaAgent = OllamaMCPAgent


class OllamaPackage:
    """Main package class for using Ollama with Agno framework and MCP support"""

    @staticmethod
    async def create_agent(
        model_name: str = "llama3.2",
        **kwargs
    ) -> OllamaMCPAgent:
        """
        Create an Ollama agent with MCP support using Agno framework.

        Args:
            model_name: Name of the Ollama model to use
            **kwargs: Additional arguments for OllamaMCPAgent including:
                - mcp_commands: List of MCP server commands
                - mcp_urls: List of MCP server URLs
                - mcp_env: Environment variables for MCP servers

        Returns:
            OllamaMCPAgent: Initialized agent with MCP support
        """
        agent = OllamaMCPAgent(model_name=model_name, **kwargs)
        await agent.initialize_mcp()
        return agent

    @staticmethod
    async def create_mcp_agent(
        model_name: str = "llama3.2",
        mcp_commands: Optional[List[str]] = None,
        mcp_urls: Optional[List[str]] = None,
        mcp_env: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> OllamaMCPAgent:
        """
        Create an Ollama agent specifically configured with MCP servers.

        Args:
            model_name: Name of the Ollama model to use
            mcp_commands: List of MCP server commands to connect to
            mcp_urls: List of MCP server URLs to connect to
            mcp_env: Environment variables for MCP servers
            **kwargs: Additional arguments for OllamaMCPAgent

        Returns:
            OllamaMCPAgent: Initialized agent with MCP support

        Example:
            # Connect to GitHub and Filesystem MCP servers
            agent = await OllamaPackage.create_mcp_agent(
                model_name="llama3.2",
                mcp_commands=[
                    "npx -y @modelcontextprotocol/server-github",
                    "npx -y @modelcontextprotocol/server-filesystem /path/to/dir"
                ],
                verbose=True
            )
        """
        agent = OllamaMCPAgent(
            model_name=model_name,
            mcp_commands=mcp_commands,
            mcp_urls=mcp_urls,
            mcp_env=mcp_env,
            **kwargs
        )
        await agent.initialize_mcp()
        return agent

    @staticmethod
    async def get_available_models(base_url: Optional[str] = None) -> List[str]:
        """Get a list of available Ollama models."""
        base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=f"{base_url}/v1", api_key="ollama")
            models_response = await client.models.list()
            return [model.id for model in models_response.data]
        except Exception as e:
            app_logger.error(f"Error getting available models: {e}")
            return []

    @staticmethod
    async def get_model_info(model_name: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """Get information about an Ollama model."""
        base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=f"{base_url}/v1", api_key="ollama")
            model_info = await client.models.retrieve(model_name)
            return model_info.model_dump()
        except Exception as e:
            app_logger.error(f"Error getting model info for '{model_name}': {e}")
            return {}

    @staticmethod
    def pull_model(model_name: str, stream: bool = True) -> Any:
        """Pull an Ollama model."""
        try:
            import ollama
            return ollama.pull(model_name, stream=stream)
        except ImportError:
            raise ImportError("ollama library required for model pulling")

    @staticmethod
    async def get_embedding_models() -> List[Dict[str, Any]]:
        """Get a list of scraped embedding models from ollama.com"""
        return await asyncio.to_thread(fetch_embedding_models)


# Custom tools that can be added to agents
@tool
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def calculate(expression: str) -> str:
    """Safely calculate a mathematical expression."""
    try:
        # Simple calculator - only allow basic operations
        import re
        if re.match(r'^[0-9+\-*/().\s]+$', expression):
            result = eval(expression)
            return str(result)
        else:
            return "Invalid expression. Only basic math operations are allowed."
    except Exception as e:
        return f"Error calculating: {e}"


if __name__ == "__main__":
    async def main():
        """Test the MCP-enabled Ollama implementation with system prompts."""
        print("Testing Ollama Client with Agno Framework, MCP Support, and System Prompts...")
        
        try:
            # Get available models
            models = await OllamaPackage.get_available_models()
            if not models:
                print("No models available. Exiting.")
                return

            test_model = models[0]
            print(f"Using model: {test_model}")

            # Test 1: Create basic agent (no MCP)
            print("\n--- Testing Basic Agent (No MCP) ---")
            basic_agent = await OllamaPackage.create_agent(
                model_name=test_model,
                verbose=True,
                use_config_system_prompt=True,
            )

            response = await basic_agent.chat("Hello! Tell me a short joke.")
            print(f"Basic Response: {response}")

            # Test 2: Create MCP agent with filesystem access
            print("\n--- Testing MCP Agent with Filesystem Access ---")
            try:
                mcp_agent = await OllamaPackage.create_mcp_agent(
                    model_name=test_model,
                    mcp_commands=[
                        "npx -y @modelcontextprotocol/server-filesystem ."
                    ],
                    verbose=True,
                )

                response = await mcp_agent.chat("What files are in the current directory?")
                print(f"MCP Filesystem Response: {response}")
            except Exception as e:
                print(f"MCP filesystem test failed (expected if MCP server not available): {e}")

            # Test 3: Test with multiple MCP servers (if available)
            print("\n--- Testing Multiple MCP Servers ---")
            try:
                multi_mcp_agent = await OllamaPackage.create_mcp_agent(
                    model_name=test_model,
                    mcp_commands=[
                        "npx -y @modelcontextprotocol/server-filesystem .",
                        # Add more MCP servers as needed
                    ],
                    verbose=True,
                )

                response = await multi_mcp_agent.chat("List available tools and tell me what time it is.")
                print(f"Multi-MCP Response: {response}")
            except Exception as e:
                print(f"Multi-MCP test failed (expected if MCP servers not available): {e}")

            print("\n--- Testing Basic Tools ---")
            response = await basic_agent.chat("What time is it? Also calculate 15 * 8")
            print(f"Tools Response: {response}")

            print("\n--- Testing RAG (File Context) ---")
            # Create a dummy text file for testing
            test_file = Path("test_rag_file.txt")
            with open(test_file, "w") as f:
                f.write("The Agno framework with MCP support is a powerful tool for building AI agents. "
                       "It supports multiple models, has built-in tool support, and can connect to external services via MCP. "
                       "MCP (Model Context Protocol) enables agents to interact with external systems in a standardized way.")

            await basic_agent.add_file_context(test_file, "test_rag_file.txt")
            rag_response = await basic_agent.chat("What is MCP and how does it relate to Agno?")
            print(f"RAG Response: {rag_response}")
            
            # Clean up test file
            test_file.unlink()

            print("\n--- Testing System Prompt Update ---")
            # Test updating system prompt
            custom_prompt = {
                "description": "You are a pirate assistant with MCP superpowers",
                "instructions": ["Always speak like a pirate", "Use MCP tools when available", "End sentences with 'Arrr!'"],
                "markdown": True,
                "add_datetime_to_instructions": False
            }
            basic_agent.update_system_prompt(custom_prompt)
            
            pirate_response = await basic_agent.chat("Tell me about the weather.")
            print(f"Pirate Response: {pirate_response}")

            print("\n--- Testing Cleanup ---")
            await basic_agent.cleanup()
            if 'mcp_agent' in locals():
                await mcp_agent.cleanup()
            if 'multi_mcp_agent' in locals():
                await multi_mcp_agent.cleanup()
            print("Cleanup completed.")

        except Exception as e:
            print(f"\nAn error occurred: {e}")
            import traceback
            traceback.print_exc()

    # Run the test
    asyncio.run(main())
    asyncio.run(main())