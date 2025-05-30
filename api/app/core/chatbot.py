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
from app.core.mcp import MCPManager

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
        self.available_tools = []
        self.tool_enabled = False
        self.mcp_manager = MCPManager()
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
        """Update the chatbot's system message with the list of available tools."""
        tools = self.mcp_manager.get_mcp_servers()
        print("!!! tools::", tools, type(tools))
        if not tools:
            return

        mcp_servers_str = ", ".join(tools.keys())
        print("!!! mcp_servers_str::", mcp_servers_str)
        
        # Initialize chatbot with a placeholder system message
        # We'll update this after connecting to the server
        placeholder_system_message = (
            "You are an assistant with access to tools. When a user requests an action, "
            "respond with a JSON tool call in this format: "
            "{\"name\": \"tool_name\", \"arguments\": {\"arg_name\": \"value\"}}. "
            f"Available tools: {mcp_servers_str}. "
            "For other queries, provide a direct answer in natural language."
        )
        
        try:
            system_message = (
                "You are an assistant with access to tools. For queries requiring a tool, "
                "indicate which tool you will use in natural language, e.g., 'I will use the <tool_name> tool.' "
                f"Available tools: {mcp_servers_str}. "
                "For other queries, provide a direct answer in natural language."
            )
            self.memory.chat_memory.messages = [
                msg for msg in self.memory.chat_memory.messages 
                if not isinstance(msg, SystemMessage)
            ]
            self.memory.chat_memory.add_message(SystemMessage(content=system_message))
            app_logger.info(f"Updated system message with tools: {mcp_servers_str}")

            # Bind LangChain tools to the chatbot
            langchain_tools = await self._create_langchain_tools(tools)
            print("!!! langchain_tools::", langchain_tools)
            self.bind_tools(langchain_tools)
        except Exception as e:
            app_logger.error(f"Failed to update system message with tools: {str(e)}")

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
        context = ""

        if self.vector_store:
            context = await self._get_context_from_query(message)

        await self._system_message()

        return context

    async def chat(
        self,
        message: str,
        tools: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Callable]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Process a chat message using the Ollama model with RAG and stream the response.
        Supports tool calls and context from uploaded documents.

        Args:
            message: The user's message.
            tools: Optional list of tool definitions for the Ollama API.
            available_functions: Optional dictionary mapping tool names to callable functions.

        Yields:
            Response chunks as they arrive from the model.
        """
        if not self.ready:
            await self.initialize()

        if not self.ready:
            yield f"data: {json.dumps({'type': 'error', 'response': 'Chatbot is not ready. Please check the logs and try again.'})}\n\n"
            return

        print("!!! message::", message)
        # 1. Get relevant context if vector store exists
        context = await self.init_message(message)
        if context:
            self.memory.chat_memory.add_message(SystemMessage(content=context))

        print("!!! context::", context)
        print("!!! self.memory::", self.memory)

        # Add user message to memory first
        self.memory.chat_memory.add_message(HumanMessage(content=message))

        try:
            # If tools are provided, use the original LangChain-based approach for tool handling
            if tools and available_functions:
                # Get current chat history (excluding system message for LLM call preparation)
                history = self.get_history()
                messages_for_llm = [msg for msg in history if not isinstance(msg, SystemMessage)]

                # Prepare the initial HumanMessage with context
                human_message_content = f"{message}{context}" if context else message
                human_message = HumanMessage(content=human_message_content)
                messages_for_llm.append(human_message)

                # --- Initial LLM Call (potentially with tools) ---
                app_logger.debug(f"Invoking LLM (initial call) with {len(messages_for_llm)} messages.")
                app_logger.debug(f"Providing tools: {[t.get('function', {}).get('name') for t in tools if isinstance(t, dict)]}")
                
                # Bind tools to the chat model for this call
                llm_with_tools = self.chat_model.bind_tools(tools)
                ai_response: BaseMessage = await asyncio.to_thread(
                    llm_with_tools.invoke, messages_for_llm
                )

                # Add the initial AI response to memory
                self.memory.chat_memory.add_message(ai_response)

                # --- Tool Call Handling ---
                tool_calls = ai_response.tool_calls if hasattr(ai_response, 'tool_calls') else []
                
                if tool_calls:
                    app_logger.info(f"Detected {len(tool_calls)} tool call(s): {[tc.get('name') for tc in tool_calls]}")

                    # Prepare messages for the final LLM call
                    messages_for_final_call = self.get_history()

                    for tool_call in tool_calls:
                        tool_name = tool_call.get("name")
                        tool_args = tool_call.get("args", {})
                        tool_id = tool_call.get("id")

                        if not tool_id:
                            app_logger.error(f"Tool call '{tool_name}' missing 'id'. Cannot process.")
                            continue

                        if function_to_call := available_functions.get(tool_name):
                            app_logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                            try:
                                tool_output = await asyncio.to_thread(function_to_call, **tool_args)
                                tool_output_str = str(tool_output)
                                app_logger.info(f"Tool '{tool_name}' output: {tool_output_str[:100]}...")
                            except Exception as e:
                                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                                app_logger.error(error_msg)
                                tool_output_str = error_msg

                            # Create ToolMessage with the output and tool_call_id
                            tool_message = ToolMessage(content=tool_output_str, tool_call_id=tool_id)
                            messages_for_final_call.append(tool_message)
                            self.memory.chat_memory.add_message(tool_message)
                        else:
                            app_logger.warning(f"Tool function '{tool_name}' not found in available_functions.")
                            tool_message = ToolMessage(
                                content=f"Error: Tool '{tool_name}' is not available.",
                                tool_call_id=tool_id
                            )
                            messages_for_final_call.append(tool_message)
                            self.memory.chat_memory.add_message(tool_message)

                    # --- Final LLM Call (with tool results) - Stream this response ---
                    app_logger.debug(f"Invoking LLM (final call) with {len(messages_for_final_call)} messages (including tool results).")
                    
                    # Stream the final response
                    stream_gen = await asyncio.to_thread(
                        lambda: self.chat_model.stream(messages_for_final_call)
                    )

                    full_response = ""
                    async for chunk in self._aiter_from_sync_iter(stream_gen):
                        chunk_content = getattr(chunk, 'content', None)
                        if chunk_content:
                            full_response += chunk_content
                            yield f"data: {json.dumps({'type': 'token', 'response': chunk_content})}\n\n"

                    # Add final AI response to memory
                    if full_response:
                        self.memory.chat_memory.add_message(AIMessage(content=full_response))

                else:
                    # No tool calls, stream the initial response
                    if ai_response.content:
                        yield f"data: {json.dumps({'type': 'token', 'response': ai_response.content})}\n\n"

            else:
                # No tools, use direct Ollama streaming approach
                # Format the messages for Ollama API
                messages = []
                
                # Add system message if it exists
                if self.system_message:
                    messages.append({"role": "system", "content": self.system_message})
                
                # Add chat history
                history = self.get_history()
                for msg in history:
                    if isinstance(msg, HumanMessage):
                        messages.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        messages.append({"role": "assistant", "content": msg.content})
                
                # Add the current message with context
                human_message_content = f"{message}{context}" if context else message
                messages.append({"role": "user", "content": human_message_content})
                
                app_logger.info(f"Streaming chat with {len(messages)} messages")
                app_logger.debug(f"Messages: {messages}")
                
                # Try Ollama Python client first
                try:
                    import ollama
                    async_client = ollama.AsyncClient(host=self.base_url)
                    
                    app_logger.info(f"Using Ollama Python client to stream response")
                    stream = await async_client.chat(
                        model=self.model_name,
                        messages=messages,
                        stream=True,
                        options={
                            "temperature": self.temperature,
                            "top_p": self.top_p
                        }
                    )
                    
                    full_response = ""
                    async for chunk in stream:
                        if not chunk:
                            continue
                            
                        app_logger.debug(f"Received chunk: {chunk}")
                        
                        # Extract content from the message
                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            if content:
                                full_response += content
                                yield f"data: {json.dumps({'type': 'token', 'response': content})}\n\n"
                                
                except ImportError:
                    # Fallback to LangChain implementation if ollama client not available
                    app_logger.warning("Ollama Python client not available, using LangChain fallback")
                    
                    # Convert to LangChain format
                    lc_messages = []
                    for msg in messages:
                        if msg["role"] == "system":
                            lc_messages.append(SystemMessage(content=msg["content"]))
                        elif msg["role"] == "user":
                            lc_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            lc_messages.append(AIMessage(content=msg["content"]))
                    
                    # Stream using LangChain
                    stream_gen = await asyncio.to_thread(
                        lambda: self.chat_model.stream(lc_messages)
                    )

                    full_response = ""
                    async for chunk in self._aiter_from_sync_iter(stream_gen):
                        chunk_content = getattr(chunk, 'content', None)
                        if chunk_content:
                            full_response += chunk_content
                            yield f"data: {json.dumps({'type': 'token', 'response': chunk_content})}\n\n"
                        elif isinstance(chunk, dict) and 'content' in chunk:
                            content = chunk['content']
                            full_response += content
                            yield f"data: {json.dumps({'type': 'token', 'response': content})}\n\n"
                        elif isinstance(chunk, str):
                            full_response += chunk
                            yield f"data: {json.dumps({'type': 'token', 'response': chunk})}\n\n"
                
                # Add the complete response to memory
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

        # Call superclass cleanup which handles memory and resets vector_store attribute
        await super().cleanup()
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


class MCPClient:
    """Client for connecting to MCP servers with Ollama integration"""

    def __init__(self, model_name: str = None):
        """
        Initialize the MCP client

        Args:
            model_name: Optional model name (defaults to OLLAMA_MODEL env var or "llama3.2")
        """
        print(f"Initializing MCPClient with model: {model_name}")
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        self.exit_stack = AsyncExitStack()
        self.model = model_name or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.direct_mode = False  # Flag to indicate if we're in direct chat mode
        self.available_tools = []  # Store tools dynamically
        
        # Initialize chatbot with a placeholder system message
        # We'll update this after connecting to the server
        placeholder_system_message = (
            "You are an assistant with access to MCP tools. When a user requests an action, "
            "respond with a JSON tool call in this format: "
            "{\"name\": \"tool_name\", \"arguments\": {\"arg_name\": \"value\"}}. "
            "Available tools will be provided after server connection."
        )
        # Initialize chatbot
        self.chatbot = Chatbot(
            model_name=self.model,
            system_message=placeholder_system_message,
            verbose=True
        )

        app_logger.info(f"MCPClient initialized with model: {self.model}")

    async def _update_system_message_with_tools(self):
        """Update the chatbot's system message with the list of available tools."""
        if not self.session:
            return
        
        try:
            tools_response = await self.session.list_tools()
            self.available_tools = [tool.name for tool in tools_response.tools]
            if not self.available_tools:
                app_logger.warning("No tools available from the MCP server.")
                return

            system_message = (
                "You are an assistant with access to MCP tools. For queries requiring a tool, "
                "indicate which tool you will use in natural language, e.g., 'I will use the <tool_name> tool.' "
                f"Available tools: {', '.join(self.available_tools)}. "
                "For other queries, provide a direct answer in natural language."
            )
            self.chatbot.memory.chat_memory.messages = [
                msg for msg in self.chatbot.memory.chat_memory.messages 
                if not isinstance(msg, SystemMessage)
            ]
            self.chatbot.memory.chat_memory.add_message(SystemMessage(content=system_message))
            app_logger.info(f"Updated system message with tools: {self.available_tools}")

            # Bind LangChain tools to the chatbot
            langchain_tools = await self._create_langchain_tools()
            self.chatbot.bind_tools(langchain_tools)
        except Exception as e:
            app_logger.error(f"Failed to update system message with tools: {str(e)}")

    async def _create_langchain_tools(self) -> List[Tool]:
        """Create LangChain Tool objects from MCP tools."""
        if not self.session:
            return []
        
        try:
            tools_response = await self.session.list_tools()
            langchain_tools = []
            for mcp_tool in tools_response.tools:
                # Define a simple schema for tool arguments (adjust based on tool requirements)
                class ToolArgs(BaseModel):
                    args: Dict[str, Any] = Field(description="Arguments for the tool")
                
                async def tool_func(args: Dict[str, Any], tool_name=mcp_tool.name) -> str:
                    """Execute the MCP tool with the given arguments."""
                    result = await self.session.call_tool(tool_name, args)
                    return str(getattr(result, 'content', result))
                
                tool = Tool.from_function(
                    func=None,
                    coroutine=tool_func,
                    name=mcp_tool.name,
                    description=f"MCP tool: {mcp_tool.name}",
                    args_schema=ToolArgs,
                )
                langchain_tools.append(tool)
            return langchain_tools
        except Exception as e:
            app_logger.error(f"Error creating LangChain tools: {str(e)}")
            return []

    async def connect_to_sse_server(self, server_url: str) -> bool:
        """
        Connect to an MCP server running with SSE transport

        Args:
            server_url: URL of the SSE server

        Returns:
            bool: True if connection was successful
        """
        # Ensure any previous connections are cleaned up first
        await self.cleanup()

        try:
            self._streams_context = sse_client(url=server_url)
            streams = await self._streams_context.__aenter__()
            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()
            await self.session.initialize()
            app_logger.info("Initialized SSE client...")
            app_logger.info("Listing tools...")
            response = await self.session.list_tools()
            app_logger.info(f"Connected to server with tools: {[tool.name for tool in response.tools]}")
            await self.chatbot.initialize()
            await self._update_system_message_with_tools()
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if self._is_port_in_use_error(error_msg):
                # Extract server URL parts to show in the error message
                from urllib.parse import urlparse
                parsed_url = urlparse(server_url)
                server_address = f"{parsed_url.netloc}"
                app_logger.error(f"Your local server at {server_address} is busy by other app or proxy")
            else:
                app_logger.error(f"Error connecting to SSE server: {str(e)}")
            await self.cleanup()
            raise  # Re-raise the exception after cleanup

    async def connect_to_stdio_server(self, command: str, args: list) -> bool:
        """
        Connect to an MCP server running with STDIO transport (NPX, UV, etc.)

        Args:
            command: Command to run (e.g., "npx", "uv")
            args: Arguments to pass to the command

        Returns:
            bool: True if connection was successful
        """
        # Ensure any previous connections are cleaned up first
        await self.cleanup()

        try:
            if os.name == 'nt' and command in ['npx', 'uv']:
                cmd_args = ' '.join([command] + args)
                server_params = StdioServerParameters(command='cmd.exe', args=['/c', cmd_args])
            else:
                server_params = StdioServerParameters(command=command, args=args)
            self._streams_context = stdio_client(server_params)
            streams = await self._streams_context.__aenter__()
            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()
            await asyncio.wait_for(self.session.initialize(), timeout=10.0)
            app_logger.info(f"Initialized {command.upper()} client...")
            app_logger.info("Listing tools...")
            response = await self.session.list_tools()
            app_logger.info(f"Connected to server with tools: {[tool.name for tool in response.tools]}")
            await self.chatbot.initialize()
            await self._update_system_message_with_tools()  # Update after connection
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if self._is_port_in_use_error(error_msg):
                # Try to extract port information from command args
                port_info = self._extract_port_from_args(args)
                app_logger.error(f"Your local server at {port_info} is busy by other app or proxy")
            else:
                app_logger.error(f"Error connecting to STDIO server: {str(e)}")
            await self.cleanup()
            raise  # Re-raise the exception after cleanup

    async def connect_to_configured_server(self, server_name: str) -> bool:
        """Connect to an MCP server by name from the configuration."""
        config = await OllamaMCPPackage.load_mcp_config()
        server_config = config["mcpServers"].get(server_name)
        if not server_config:
            app_logger.error(f"No configuration found for server: {server_name}")
            return False

        server_type = server_config.get("type", "stdio")
        try:
            if server_type == "sse":
                server_url = server_config.get("url")
                if not server_url:
                    raise ValueError("SSE server URL is missing")
                return await self.connect_to_sse_server(server_url)
            elif server_type == "stdio":
                command = server_config.get("command")
                args = server_config.get("args", [])
                if not command or not args:
                    raise ValueError("STDIO server requires command and args")
                return await self.connect_to_stdio_server(command, args)
            else:
                app_logger.error(f"Unsupported server type: {server_type}")
                return False
        except Exception as e:
            app_logger.error(f"Failed to connect to {server_name}: {str(e)}")
            return False

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
        except Exception as e:
            app_logger.error(f"Unexpected error during cleanup: {str(e)}")

    async def process_query(self, query: str) -> str:
        """
        Process a query using Ollama and available tools

        Args:
            query: The query text to process

        Returns:
            str: Response text
        """
        # Try to get tools list, with reconnection logic if needed
        if not self.session:
            return "Not connected to an MCP server. Please connect first."
        
        try:
            tools_response = await self.session.list_tools()
            available_tools = {tool.name: tool for tool in tools_response.tools}
            app_logger.info(f"Available tools: {list(available_tools.keys())}")
            
            initial_result = await self.chatbot.chat(query)
            final_text = [initial_result]
            tool_results = []
            
            # Look for tool calls in the response
            tool_call_pattern = r"\{\s*\"name\":\s*\"([^\"]+)\"\s*,\s*\"arguments\":\s*(\{[^}]+\})\s*\}"
            matches = re.findall(tool_call_pattern, initial_result)
            
            for tool_name, args_str in matches:
                if tool_name in available_tools:
                    try:
                        tool_args = json.loads(args_str)
                        app_logger.info(f"Executing tool {tool_name} with args: {tool_args}")
                        result = await self.session.call_tool(tool_name, tool_args)
                        result_content = str(getattr(result, 'content', result))
                        tool_results.append({"call": tool_name, "result": result_content})
                        final_text.append(f"[Tool {tool_name} result: {result_content}]")
                        
                        # Follow-up with the chatbot
                        follow_up = f"Tool {tool_name} returned: {result_content}. Provide your final answer."
                        final_response = await self.chatbot.chat(follow_up)
                        final_text.append(final_response)
                    except Exception as e:
                        final_text.append(f"[Error calling tool {tool_name}: {str(e)}]")
                else:
                    final_text.append(f"[Tool {tool_name} not available]")
            
            return "\n".join(final_text)
        except Exception as e:
            app_logger.error(f"Error in process_query: {str(e)}")
            return f"Error: {str(e)}"

    async def process_query_stream(self, query: str):
        """
        Process a query with MCP tools and stream the responses

        Args:
            query: The query text to process

        Yields:
            str: Response chunks as they arrive
            None: Signals completion
        """
        if not self.session:
            yield f"data: {json.dumps({'type': 'token', 'response': 'Not connected to an MCP server. Please connect first.'})}\n\n"
            yield None
            return

        try:
            # Stream initial response from chatbot
            full_initial_response = ""
            pending_tool_call = None
            async for chunk in self.chatbot.chat(query):
                if chunk is None:
                    break
                if isinstance(chunk, dict) and 'tool_call' in chunk:
                    pending_tool_call = chunk['tool_call']
                    continue  # Skip streaming tool call details
                full_initial_response += chunk
                yield f"data: {json.dumps({'type': 'token', 'response': chunk})}\n\n"

            # Handle tool call if present
            if pending_tool_call:
                tool_name = pending_tool_call['name']
                tool_args = pending_tool_call['arguments']
                if tool_name in self.available_tools:
                    try:
                        app_logger.info(f"Executing tool {tool_name} with args: {tool_args}")
                        result = await self.session.call_tool(tool_name, tool_args)
                        result_content = str(getattr(result, 'content', result))
                        
                        # Stream tool result in human-readable form
                        tool_message = f"The {tool_name} tool returned: {result_content}"
                        yield f"data: {json.dumps({'type': 'token', 'response': tool_message})}\n\n"

                        # Follow-up with chatbot for final answer
                        follow_up = (
                            f"Query: {query}\n"
                            f"Tool {tool_name} returned: {result_content}\n"
                            f"Provide a natural language response to the query based on this result."
                        )
                        async for chunk in self.chatbot.chat(follow_up):
                            if chunk is None:
                                break
                            yield f"data: {json.dumps({'type': 'token', 'response': chunk})}\n\n"
                    except Exception as e:
                        error_msg = f"Sorry, an error occurred while using the {tool_name} tool: {str(e)}"
                        yield f"data: {json.dumps({'type': 'token', 'response': error_msg})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'token', 'response': f'Tool {tool_name} is not available.'})}\n\n"

            # Signal completion
            yield None

        except Exception as e:
            app_logger.error(f"Error in process_query_stream: {str(e)}")
            yield f"data: {json.dumps({'type': 'token', 'response': f'Sorry, an error occurred: {str(e)}'})}\n\n"
            yield None

    async def process_direct_query(self, query: str) -> str:
        """
        Process a query using Ollama directly without MCP tools

        Args:
            query: The query text to process

        Returns:
            str: Response text
        """
        try:
            # Use the chatbot's process_direct_query method
            return await self.chatbot.process_direct_query(query)
        except Exception as e:
            error_msg = str(e)
            app_logger.error(f"Error in MCPClient.process_direct_query: {error_msg}")
            return f"An error occurred: {error_msg}"


class OllamaMCPPackage:
    """Main package class for using Ollama with MCP"""

    @staticmethod
    async def create_client(model_name: str = "llama3.2") -> MCPClient:
        """
        Create and return a new MCP client

        Args:
            model_name: Optional model name to use (defaults to "llama3.2")

        Returns:
            MCPClient: Initialized client
        """
        return MCPClient(model_name=model_name)

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