import sys
import os
import inspect

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

# Now proceed with imports that rely on the project structure
# pip install "mcp==1.3.0" langchain-ollama langchain-core

import asyncio
import json
import os
from typing import Optional, List, Dict, Any, Union, Callable, AsyncGenerator
from contextlib import AsyncExitStack
import logging
from pathlib import Path
import tempfile
import shutil
from pydantic import BaseModel, Field

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from app.core.mcp.servers import MCPServersConfig

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ChatMessage,
    FunctionMessage,
    ToolMessage,
    BaseMessage
)
from langchain_core.messages import AIMessageChunk, ToolCall
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool, Tool
from langchain_ollama import ChatOllama
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import anyio
from tqdm import tqdm # Added import
import re


# Import the logger
from app.utils.logger import app_logger
from app.core.config import read_ollama_config

# Added imports for RAG
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.docstore.document import Document

from app.core.mcp.manager import MCPClientManager

# Added import for PDF processing
try:
    import pypdf
except ImportError:
    pypdf = None # Handle optional dependency

# Import embedding models scraper function
from app.services.scrape_ollama import fetch_embedding_models

load_dotenv()  # load environment variables from .env

class Chatbot():
    """Chatbot implementation using Ollama and LangChain"""

    def __init__(
        self,
        model_name: str = "llama3.2",
        vision_model_name: str = "granite3.2-vision",
        system_message: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        verbose: bool = False,
        # Added embedding model parameter
        embedding_model_name: str = "nomic-embed-text",
        # Added text splitter parameters
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
    ):
        """
        Initialize the Ollama chatbot.

        Args:
            model_name: Name of the Ollama model to use
            vision_model_name: Name of the Ollama vision model to use
            system_message: Optional system message to set context
            base_url: Base URL for the Ollama API (default: http://localhost:11434)
            temperature: Temperature parameter for generation
            top_p: Top-p parameter for generation
            verbose: Whether to output verbose logs
            embedding_model_name: Name of the Ollama embedding model to use
            chunk_size: Size of text chunks for vector store
            chunk_overlap: Overlap between text chunks
        """
        # Initialize attributes directly instead of calling super().__init__
        self.model_name = model_name
        self.vision_model_name = vision_model_name
        self.system_message = system_message
        self.verbose = verbose
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = temperature
        self.top_p = top_p
        self.chat_model = None
        self.ready = False
        # Initialize embeddings and text splitter
        self.embedding_model_name = embedding_model_name
        self.embeddings = OllamaEmbeddings(model=self.embedding_model_name, base_url=self.base_url)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=['\n\n', '\n', '. ', ' ', ''] # More robust separators
        )
        self._temp_dir_for_vs = None # To hold temp directory object
        self.tools = []
        self.tool_enabled = False
        self.session: Optional[ClientSession] = None
        # Added vector store attribute
        self.vector_store: Optional[FAISS] = None
        self.vector_store_path: Optional[Path] = None # Store path for persistence if needed
        # Initialize memory for conversation
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            chat_memory=ChatMessageHistory(),
            return_messages=True
        )

    async def initialize(self) -> None:
        """Initialize the Ollama chatbot with tool binding support."""
        try:
            self.chat_model = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                streaming=True
            )
            if self.verbose:
                app_logger.info(f"Initialized Ollama with model: {self.model_name}")
            self.ready = True

            # Set system message if provided
            if self.system_message:
                current_history = self.memory.chat_memory.messages
                if not current_history or not isinstance(current_history[0], SystemMessage):
                    self.memory.chat_memory.add_message(SystemMessage(content=self.system_message))
                elif isinstance(current_history[0], SystemMessage) and current_history[0].content != self.system_message:
                    current_history[0] = SystemMessage(content=self.system_message)
        except Exception as e:
            app_logger.error(f"Failed to initialize Ollama chatbot: {str(e)}")
            self.ready = False
            raise

    async def add_file_context(self, file_path: Union[str, Path], file_name: str):
        """
        Processes a file, extracts text, creates embeddings, and updates the vector store.

        Args:
            file_path: Path to the uploaded file.
            file_name: Original name of the file (used for metadata).
        """
        if not self.ready:
            await self.initialize()
        if not self.ready:
             raise RuntimeError("Chatbot could not be initialized.")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found at {file_path}")

        app_logger.info(f"Processing file for context: {file_name} ({file_path.suffix})")
        text = ""
        try:
            if file_path.suffix == '.pdf':
                if pypdf:
                    reader = pypdf.PdfReader(file_path)
                    text = "".join(page.extract_text() for page in reader.pages if page.extract_text())
                else:
                     app_logger.error("pypdf is not installed. Cannot process PDF files.")
                     raise ImportError("pypdf is required for PDF processing.")
            elif file_path.suffix in ['.txt', '.md']:
                text = file_path.read_text(encoding='utf-8')
            else:
                app_logger.warning(f"Unsupported file type: {file_path.suffix}")
                return # Or raise error

            if not text:
                app_logger.warning(f"No text extracted from file: {file_name}")
                return

            # Split text into documents
            documents = self.text_splitter.create_documents(
                [text],
                metadatas=[{"source": file_name}] # Add source metadata
            )
            app_logger.info(f"Split file {file_name} into {len(documents)} documents.")

            # Create or update FAISS vector store
            if not self.vector_store:
                # Create a temporary directory for the FAISS index
                # Store the TemporaryDirectory object to ensure it's cleaned up later
                self._temp_dir_for_vs = tempfile.TemporaryDirectory()
                self.vector_store_path = Path(self._temp_dir_for_vs.name) / "faiss_index"

                app_logger.info(f"Creating new vector store at {self.vector_store_path}")
                self.vector_store = await asyncio.to_thread(
                    FAISS.from_documents, documents, self.embeddings
                )
                # Save locally to the temp path
                await asyncio.to_thread(self.vector_store.save_local, str(self.vector_store_path))

            else:
                 app_logger.info(f"Adding documents to existing vector store.")
                 # FAISS doesn't have an async add_documents, run in thread
                 await asyncio.to_thread(self.vector_store.add_documents, documents)
                 # Re-save after adding
                 await asyncio.to_thread(self.vector_store.save_local, str(self.vector_store_path))

            app_logger.info(f"Successfully added context from {file_name} to vector store.")

        except Exception as e:
            app_logger.error(f"Error processing file {file_name}: {str(e)}", exc_info=True)
            # Clean up temp file if it exists and is the one we're processing
            # Note: The API layer should handle cleanup of the originally uploaded temp file
            raise # Re-raise the exception to be caught by the API layer

    async def _system_message(self):
        """
        Update the chatbot's system message with available tools and clear instructions for use.

        Ensures the system message guides the model to:
        - Answer directly for informational queries.
        - Use tools for action-oriented queries with a clear JSON tool call format.
        - Indicate tool usage in natural language before returning the tool call.
        """
        try:
            # Get formatted tool descriptions
            mcp_manager = MCPClientManager()
            tool_instruction = await mcp_manager.get_all_formatted_tools()
            
            # Define system message
            system_message = (
                "You are a helpful AI assistant with access to specialized tools. "
                "Your role is to understand user requests and either provide direct answers or use appropriate tools to fulfill their needs. "
                "Be precise with tool usage and always explain your actions clearly."
                f"\n{tool_instruction}"
            )

            # Clear existing system messages and update with new one
            self.memory.chat_memory.messages = [
                msg for msg in self.memory.chat_memory.messages 
                if not isinstance(msg, SystemMessage)
            ]
            self.memory.chat_memory.add_message(SystemMessage(content=system_message))
            # Update the instance attribute to keep it in sync
            self.system_message = system_message

            # # Bind LangChain tools if available
            # if tools:
            #     langchain_tools = await self._create_langchain_tools(tools)
            #     app_logger.debug(f"Binding LangChain tools: {[tool.name for tool in langchain_tools]}")
            #     self.bind_tools(langchain_tools)
            # else:
            #     app_logger.info("No tools available, skipping tool binding")

        except Exception as e:
            app_logger.error(f"Failed to update system message: {str(e)}")
            # Set a fallback system message to ensure functionality
            fallback_message = (
                "You are a helpful assistant. Answer user questions accurately in natural language. "
                "No tools are currently available due to an initialization error."
            )
            self.memory.chat_memory.messages = [
                msg for msg in self.memory.chat_memory.messages 
                if not isinstance(msg, SystemMessage)
            ]
            self.memory.chat_memory.add_message(SystemMessage(content=fallback_message))
            # Update the instance attribute to keep it in sync
            self.system_message = fallback_message
            app_logger.info("Set fallback system message due to error")

    async def _get_context_from_query(self, query: str, k: int = 3) -> str:
        """Retrieve relevant context from the vector store"""
        if not self.vector_store:
            return ""

        try:
            app_logger.info(f"Searching vector store for query: {query[:50]}...")
            # Run similarity search in a thread
            results = await asyncio.to_thread(
                 self.vector_store.similarity_search, query, k=k
            )
            if results:
                context = "\n---\n".join([doc.page_content for doc in results])
                app_logger.info(f"Retrieved {len(results)} context snippets.")
                # print(f"CONTEXT:\n{context}\n---------") # for debugging
                return f"\n\nRelevant Context from Uploaded Documents:\n---\n{context}\n---"
            else:
                app_logger.info("No relevant context found in vector store.")
                return ""
        except Exception as e:
            app_logger.error(f"Error during similarity search: {str(e)}")
            return ""
    
    async def init_message(self, message: str):
        """
        Initialize the message with the system message and context
        """
        context = await self._get_context_from_query(message) if self.vector_store else ""
        await self._system_message()
        return context

    async def chat(self, message: str) -> AsyncGenerator[str, None]:
        """
        Process a chat message using the Ollama model with RAG and stream the response.
        Focuses on direct chat functionality with context from uploaded documents.

        Args:
            message: The user's message.

        Yields:
            Response chunks as they arrive from the model.
        """
        if not self.ready:
            await self.initialize()
            if not self.ready:
                yield f"data: {json.dumps({'type': 'error', 'response': 'Chatbot is not ready. Please check the logs and try again.'})}\n\n"
                return

        print("!!! message::", message)
        context = await self.init_message(message)
        if context:
            self.memory.chat_memory.add_message(SystemMessage(content=context))

        print("!!! context::", context)
        print("!!! self.memory::", self.memory)
        self.memory.chat_memory.add_message(HumanMessage(content=message))

        try:
            # Build messages directly from memory instead of using static system_message
            messages = []
            for msg in self.memory.chat_memory.messages:
                if isinstance(msg, SystemMessage):
                    messages.append({"role": "system", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})

            app_logger.info(f"Streaming chat with {len(messages)} messages")
            app_logger.debug(f"Messages: {messages}")

            try:
                import ollama
                async_client = ollama.AsyncClient(host=self.base_url)
                app_logger.info(f"Using Ollama Python client to stream response")
                stream = await async_client.chat(
                    model=self.model_name, messages=messages, stream=True,
                    options={"temperature": self.temperature, "top_p": self.top_p}
                )
                full_response = ""
                async for chunk in stream:
                    if not chunk:
                        continue
                    app_logger.debug(f"Received chunk: {chunk}")
                    if 'message' in chunk and 'content' in chunk['message']:
                        content = chunk['message']['content']
                        if content:
                            full_response += content
                            yield f"data: {json.dumps({'type': 'token', 'response': content})}\n\n"
            except ImportError:
                app_logger.warning("Ollama Python client not available, using LangChain fallback")
                lc_msgs = []
                for m in messages:
                    role, content = m["role"], m["content"]
                    lc_msgs.append(SystemMessage(content=content) if role == "system" else HumanMessage(content=content) if role == "user" else AIMessage(content=content))
                stream_gen = await asyncio.to_thread(lambda: self.chat_model.stream(lc_msgs))
                full_response = ""
                async for chunk in self._aiter_from_sync_iter(stream_gen):
                    content = getattr(chunk, 'content', None) or (chunk.get('content') if isinstance(chunk, dict) else chunk if isinstance(chunk, str) else None)
                    if content:
                        full_response += content
                        yield f"data: {json.dumps({'type': 'token', 'response': content})}\n\n"

            if full_response:
                app_logger.info(f"Streamed complete response (first 100 chars): {full_response[:100]}")
                self.memory.chat_memory.add_message(AIMessage(content=full_response))
            else:
                app_logger.warning("No response content received from stream")
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'response': error_msg})}\n\n"

    def bind_tools(self, tools: List[Tool]):
        """Bind LangChain tools to the chat model."""
        self.tools = tools
        self.tool_enabled = bool(tools)
        if tools:
            self.chat_model = self.chat_model.bind_tools(tools)
            app_logger.info(f"Bound tools: {[tool.name for tool in tools]}")

    async def _aiter_from_sync_iter(self, sync_iter):
        """Convert a synchronous iterator to an async iterator"""
        try:
            while True:
                item = await asyncio.to_thread(next, sync_iter, StopAsyncIteration)
                if item is StopAsyncIteration:
                    break
                yield item
        except Exception as e:
            app_logger.error(f"Error in async iterator conversion: {str(e)}")
            raise

    async def cleanup(self) -> None:
        """Clean up resources used by the Ollama chatbot, including temp vector store"""
        # Clean up temporary directory if it was created
        if self._temp_dir_for_vs:
            try:
                self._temp_dir_for_vs.cleanup() # This handles directory removal
                app_logger.info(f"Cleaned up temporary directory for vector store: {self._temp_dir_for_vs.name}")
            except Exception as e:
                 app_logger.error(f"Error cleaning up temporary directory {self._temp_dir_for_vs.name}: {e}")
            finally:
                 self._temp_dir_for_vs = None
                 self.vector_store_path = None # Path becomes invalid after cleanup

        # Reset chatbot attributes
        self.chat_model = None
        self.ready = False
        # Ensure vector_store is None after cleanup
        self.vector_store = None

    def get_history(self) -> List[BaseMessage]:
        """Get the conversation history"""
        memory_variables = self.memory.load_memory_variables({})
        return memory_variables.get("history", [])

    def clear_history(self) -> None:
        """Clear the conversation history"""
        self.memory.clear()

    async def chat_with_image(self,
                              message: str,
                              image_paths: List[Union[str, Path]],
                              temperature: Optional[float] = None,
                              top_p: Optional[float] = None) -> str:
        """
        Process a message with image context using the specified vision model.

        Args:
            message: The user's text message.
            image_paths: A list of paths to the images.
            temperature: Optional temperature override for this call.
            top_p: Optional top_p override for this call.

        Returns:
            The response string from the vision model.
        """
        if not self.ready:
            await self.initialize()

        if not self.ready:
            return "Chatbot is not ready. Please check the logs and try again."

        if not self.vision_model_name:
            return "No vision model specified for this chatbot."

        # Ensure image paths are strings
        image_paths_str = [str(p) for p in image_paths]

        # Prepare messages for the Ollama API
        messages = [
            {
                'role': 'user',
                'content': message,
                'images': image_paths_str,
            }
        ]

        try:
            import ollama
            async_client = ollama.AsyncClient(host=self.base_url)

            app_logger.info(f"Sending request to vision model: {self.vision_model_name}")
            response = await async_client.chat(
                model=self.vision_model_name,
                messages=messages,
                options={
                    "temperature": temperature if temperature is not None else self.temperature,
                    "top_p": top_p if top_p is not None else self.top_p
                }
            )

            response_content = response.get('message', {}).get('content', '')
            app_logger.info(f"Received vision response: {response_content[:100]}...")

            # Add interaction to memory (simplify image representation for memory)
            image_context_placeholder = f"[User provided {len(image_paths)} image(s)]"
            self.memory.chat_memory.add_message(HumanMessage(content=f"{message} {image_context_placeholder}"))
            self.memory.chat_memory.add_message(AIMessage(content=response_content))

            return response_content

        except ImportError:
            error_msg = "The 'ollama' library is required for vision capabilities. Please install it: pip install ollama"
            app_logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error during vision chat: {str(e)}"
            app_logger.error(error_msg, exc_info=True)
            return error_msg

    async def process_direct_query(self, query: str) -> str:
        """
        Process a query using Ollama directly without MCP tools

        Args:
            query: The query text to process

        Returns:
            str: Response text
        """
        try:
            # Collect the streamed response into a single string
            full_response = ""
            async for chunk in self.chat(query):
                if chunk and chunk.startswith('data: '):
                    try:
                        chunk_data = json.loads(chunk.replace('data: ', ''))
                        if chunk_data.get('type') == 'token':
                            full_response += chunk_data.get('response', '')
                    except json.JSONDecodeError:
                        # Skip invalid JSON chunks
                        continue
            
            return full_response if full_response else "No response received"
            
        except Exception as e:
            error_msg = str(e)

            # Check for server connection issues (502 status code)
            if "status code: 502" in error_msg:
                # Extract server information from environment
                server_url = os.getenv("OLLAMA_HOST", "localhost:11434")
                error_message = f"Your local Ollama server at {server_url} is busy by other app or proxy"
                app_logger.error(f"Error in process_direct_query: {error_message}")
                return error_message

            # For other errors, log the full error
            app_logger.error(f"Error in process_direct_query: {error_msg}")
            return f"An error occurred: {error_msg}"
    
    async def _create_langchain_tools(self, tools: List[Any]) -> List[Tool]:
        """Create LangChain Tool objects from MCP tools."""
        if not tools:
            return []
        
        try:
            langchain_tools = []
            print("!!! tools::", tools, type(tools))
            for tool_name, mcp_tool in tools.items():
                # Define a simple schema for tool arguments (adjust based on tool requirements)
                class ToolArgs(BaseModel):
                    args: Dict[str, Any] = Field(description="Arguments for the tool")

                
                async def tool_func(args: Dict[str, Any], tool_name=tool_name):
                    """Execute the MCP tool with the given arguments."""
                    result = await self.session.call_tool(tool_name, args)
                    return str(getattr(result, 'content', result))
                
                tool = Tool.from_function(
                    func=None,
                    coroutine=tool_func,
                    name=tool_name,
                    description=f"MCP tool: {tool_name}",
                    args_schema=ToolArgs,
                )
                langchain_tools.append(tool)
            return langchain_tools
        except Exception as e:
            app_logger.error(f"Error creating LangChain tools: {str(e)}")
            return []


class OllamaMCPPackage:
    """Main package class for using Ollama with MCP"""

    @staticmethod
    async def create_standalone_chatbot(
        model_name: str = "llama3.2",
        vision_model_name: str = "granite3.2-vision",
        system_message: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7
    ) -> Chatbot:
        """
        Create and initialize a standalone Ollama chatbot

        Args:
            model_name: Name of the Ollama model to use
            vision_model_name: Name of the Ollama vision model to use
            system_message: Optional system message to set context
            base_url: Base URL for the Ollama API
            temperature: Temperature parameter for generation

        Returns:
            Chatbot: Initialized chatbot
        """
        chatbot = Chatbot(
            model_name=model_name,
            vision_model_name=vision_model_name,
            system_message=system_message,
            base_url=base_url,
            temperature=temperature
        )
        await chatbot.initialize()
        return chatbot

    @staticmethod
    async def get_available_models(base_url: Optional[str] = None) -> List[str]:
        """
        Get a list of available Ollama models

        Args:
            base_url: Optional base URL for the Ollama API

        Returns:
            List[str]: List of available model names
        """
        import requests

        try:
            base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
            response = requests.get(f"{base_url}/api/tags")
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except Exception as e:
            app_logger.error(f"Error getting available models: {str(e)}")
            return []

    @staticmethod
    async def get_model_info(model_name: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a curated, specific set of information about an Ollama model.

        Args:
            model_name: The name of the model to get information for.
            base_url: Optional base URL for the Ollama API.

        Returns:
            Dict[str, Any]: A dictionary containing only the specified model details,
                           or an empty dictionary if an error occurs or data is missing.
        """
        try:
            import ollama
            # Use AsyncClient for direct async call
            client = ollama.AsyncClient(host=base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434"))
            # Directly await the async show method
            full_info = await client.show(model_name)

            details = full_info.get('details', {})
            modelinfo = full_info.get('modelinfo', {})

            # Handle potential ModelDetails object
            if not isinstance(details, dict) and hasattr(details, '__dict__'):
                details_dict = vars(details)
            elif isinstance(details, dict):
                details_dict = details
            else:
                details_dict = {}

            # Extract and map specific fields
            curated_info = {
                "family": details_dict.get('family'),
                "parameter_size": details_dict.get('parameter_size'),
                "quantization_level": details_dict.get('quantization_level'),
                "model_name": modelinfo.get('general.basename'),
                "languages_supported": modelinfo.get('general.languages'),
                "parameter_count": modelinfo.get('general.parameter_count'),
                "size_label": modelinfo.get('general.size_label'),
                "tags": modelinfo.get('general.tags'),
                "type": modelinfo.get('general.type'),
                "context_length": modelinfo.get('llama.context_length'),
                "embedding_length": modelinfo.get('llama.embedding_length'),
                "vocab_size": modelinfo.get('llama.vocab_size'),
            }

            # Remove keys where the value is None (if the field was missing in the source)
            cleaned_info = {k: v for k, v in curated_info.items() if v is not None}

            return cleaned_info

        except ImportError:
            app_logger.error("The 'ollama' library is required but not installed. Please install it using 'pip install ollama'.")
            return {}
        except Exception as e:
            # Catch potential ResponseError from the ollama library
            if "ollama.ResponseError" in str(type(e)) and "not found" in str(e).lower():
                 app_logger.warning(f"Model '{model_name}' not found via API.")
                 # Return empty dict which the API endpoint will turn into 404
            else:
                 app_logger.error(f"Error getting model info for '{model_name}': {str(e)}")
            # Propagate specific errors or return empty dict for general ones
            # Check if it's the specific ResponseError for 'not found'
            if "ollama.ResponseError" in str(type(e)) and "not found" in str(e).lower():
                return {}
            # Re-raise other exceptions to be caught by the API endpoint handler
            raise e

    @staticmethod
    def pull_model(model_name: str, stream: bool = True) -> Any:
        """
        Pull the specified Ollama model, returning a generator of progress dicts.
        """
        from ollama import pull
        return pull(model_name, stream=stream)

    @staticmethod
    async def get_embedding_models() -> List[Dict[str, Any]]:
        """Get a list of scraped embedding models from ollama.com"""
        return await asyncio.to_thread(fetch_embedding_models)

if __name__ == "__main__":
    async def main():

        # Test pulling a model with tqdm
        print("--- Testing Model Pull with tqdm ---")
        current_digest, bars = '', {}
        # model_to_pull = "llama3.2" # Or change to another model like "moondream"
        model_to_pull = "moondream"
        try:
            for progress in OllamaMCPPackage.pull_model(model_to_pull):
                digest = progress.get('digest', '')
                if digest != current_digest and current_digest in bars:
                    bars[current_digest].close()

                if not digest:
                    # Handle status messages (like 'pulling manifest')
                    status = progress.get('status')
                    if status:
                        print(status)
                    continue

                if digest not in bars and (total := progress.get('total')):
                    # Use a short digest for the description
                    short_digest = digest.split(':')[-1][:12] if ':' in digest else digest[:12]
                    bars[digest] = tqdm(total=total, desc=f'pulling {short_digest}', unit='B', unit_scale=True)

                if digest in bars and (completed := progress.get('completed')):
                    bars[digest].update(completed - bars[digest].n)

                current_digest = digest

        finally:
             # Ensure all bars are closed
             for bar in bars.values():
                 bar.close()
        print("\n")


    asyncio.run(main())