# pip install langchain-ollama langchain-core

import asyncio
import os
from typing import Optional, List, Any
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage
)
from langchain_ollama import ChatOllama
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv

# Import the logger
from logger import app_logger

load_dotenv()  # load environment variables from .env

class BaseChatbot:
    """Base class for chatbot implementations"""

    def __init__(
        self,
        model_name: str = "llama3.2",
        system_message: Optional[str] = None,
        verbose: bool = False,
    ):
        self.model_name = model_name
        self.system_message = system_message
        self.verbose = verbose
        self.memory = ConversationBufferMemory(return_messages=True)

    async def initialize(self) -> None:
        """Initialize the chatbot - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement initialize()")

    async def chat(self, message: str) -> str:
        """Process a chat message and return the response"""
        raise NotImplementedError("Subclasses must implement chat()")

    async def cleanup(self) -> None:
        """Clean up any resources used by the chatbot"""
        self.memory = ConversationBufferMemory(return_messages=True)

    def get_history(self) -> List[BaseMessage]:
        """Get the conversation history"""
        memory_variables = self.memory.load_memory_variables({})
        return memory_variables.get("history", [])

    def clear_history(self) -> None:
        """Clear the conversation history"""
        self.memory.clear()

class OllamaChatbot(BaseChatbot):
    """Chatbot implementation using Ollama and LangChain"""

    def __init__(
        self,
        model_name: str = "llama3.2",
        system_message: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        verbose: bool = False,
    ):
        super().__init__(model_name, system_message, verbose)
        self.base_url = base_url or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.temperature = temperature
        self.top_p = top_p
        self.chat_model = None
        self.ready = False

    async def initialize(self) -> None:
        try:
            self.chat_model = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature,
                top_p=self.top_p,
                streaming=True
            )

            if self.verbose:
                app_logger.info(f"Initializing Ollama with model: {self.model_name}")

            self.ready = True

            if self.system_message:
                self.memory.chat_memory.add_message(SystemMessage(content=self.system_message))

        except Exception as e:
            app_logger.error(f"Failed to initialize Ollama chatbot: {str(e)}")
            self.ready = False
            raise

    async def chat(self, message: str) -> str:
        if not self.ready:
            await self.initialize()

        if not self.ready:
            return "Chatbot is not ready. Please check the logs and try again."

        history = self.get_history()
        self.memory.chat_memory.add_message(HumanMessage(content=message))

        try:
            messages = history + [HumanMessage(content=message)]
            response = await asyncio.to_thread(
                self.chat_model.invoke,
                messages
            )
            self.memory.chat_memory.add_message(AIMessage(content=response.content))
            return response.content

        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            app_logger.error(error_msg)
            return error_msg

    async def chat_stream(self, message: str):
        """Process a chat message and stream the responses"""
        if not self.ready:
            await self.initialize()

        if not self.ready:
            yield "Chatbot is not ready. Please check the logs and try again."
            return

        history = self.get_history()
        self.memory.chat_memory.add_message(HumanMessage(content=message))

        try:
            messages = history + [HumanMessage(content=message)]
            stream_gen = await asyncio.to_thread(
                lambda: self.chat_model.stream(messages)
            )

            full_response = ""

            async for chunk in self._aiter_from_sync_iter(stream_gen):
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    yield chunk.content
                elif isinstance(chunk, dict) and 'content' in chunk:
                    full_response += chunk['content']
                    yield chunk['content']
                elif isinstance(chunk, str):
                    full_response += chunk
                    yield chunk

            self.memory.chat_memory.add_message(AIMessage(content=full_response))
            yield None

        except Exception as e:
            error_msg = f"Error processing streaming message: {str(e)}"
            app_logger.error(error_msg)
            yield error_msg
            yield None

    async def _aiter_from_sync_iter(self, sync_iter):
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
        await super().cleanup()
        self.chat_model = None
        self.ready = False 

if __name__ == "__main__":
    async def main():
        # Initialize the chatbot
        chatbot = OllamaChatbot(
            model_name="llama3.2",
            system_message="You are a helpful AI assistant.",
            verbose=True
        )
        
        # Example of regular chat
        print("\n=== Regular Chat Example ===")
        response = await chatbot.chat("Hello! How are you?")
        print(f"Bot: {response}")
        
        # Example of streaming chat
        print("\n=== Streaming Chat Example ===")
        print("Bot: ", end="", flush=True)
        async for chunk in chatbot.chat_stream("Tell me a short joke"):
            if chunk is not None:
                print(chunk, end="", flush=True)
        print("\n")
        
        # Example of getting chat history
        print("\n=== Chat History ===")
        history = chatbot.get_history()
        for message in history:
            role = "System" if isinstance(message, SystemMessage) else \
                   "Human" if isinstance(message, HumanMessage) else "AI"
            print(f"{role}: {message.content}")
        
        # Cleanup
        await chatbot.cleanup()

    # Run the example
    asyncio.run(main())