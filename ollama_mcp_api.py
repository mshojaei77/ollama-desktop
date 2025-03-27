"""
Ollama MCP API - Integration example with FastAPI
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Union

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ollama_mcp import OllamaMCPPackage, OllamaChatbot, MCPClient, app_logger

# Initialize FastAPI app
app = FastAPI(
    title="Ollama MCP API",
    description="API for interacting with Ollama models and MCP tools",
    version="1.0.0"
)

# Global state for clients and chatbots
active_clients: Dict[str, MCPClient] = {}
active_chatbots: Dict[str, OllamaChatbot] = {}


# ----- Pydantic Models for Request/Response -----

class ChatRequest(BaseModel):
    message: str
    session_id: str
    
class ChatResponse(BaseModel):
    response: str
    session_id: str

class InitializeRequest(BaseModel):
    model_name: str = "llama3.2"
    system_message: Optional[str] = None
    session_id: Optional[str] = None
    
class InitializeResponse(BaseModel):
    session_id: str
    status: str
    model: str

class MCPServerConnectRequest(BaseModel):
    server_type: str  # "sse" or "stdio"
    server_url: Optional[str] = None  # For SSE
    command: Optional[str] = None     # For STDIO
    args: Optional[List[str]] = None  # For STDIO
    session_id: Optional[str] = None
    model_name: str = "llama3.2"

class StatusResponse(BaseModel):
    status: str
    active_sessions: List[str]
    message: Optional[str] = None


# ----- Helper Functions -----

def generate_session_id() -> str:
    """Generate a unique session ID"""
    import uuid
    return f"session-{uuid.uuid4()}"

async def cleanup_session(session_id: str):
    """Clean up resources for a session"""
    if session_id in active_clients:
        await active_clients[session_id].cleanup()
        del active_clients[session_id]
        app_logger.info(f"Cleaned up client session: {session_id}")
        
    if session_id in active_chatbots:
        await active_chatbots[session_id].cleanup()
        del active_chatbots[session_id]
        app_logger.info(f"Cleaned up chatbot session: {session_id}")


# ----- API Endpoints -----

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "service": "Ollama MCP API",
        "active_sessions": len(active_clients) + len(active_chatbots)
    }

@app.post("/chat/initialize", response_model=InitializeResponse)
async def initialize_chatbot(request: InitializeRequest):
    """Initialize a standalone Ollama chatbot"""
    try:
        session_id = request.session_id or generate_session_id()
        
        # Clean up existing session if it exists
        if session_id in active_chatbots:
            await cleanup_session(session_id)
        
        # Create new chatbot
        chatbot = await OllamaMCPPackage.create_standalone_chatbot(
            model_name=request.model_name,
            system_message=request.system_message
        )
        
        # Store in active sessions
        active_chatbots[session_id] = chatbot
        
        return InitializeResponse(
            session_id=session_id,
            status="ready",
            model=request.model_name
        )
    except Exception as e:
        app_logger.error(f"Error initializing chatbot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing chatbot: {str(e)}")

@app.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    """Send a message to a chatbot"""
    if request.session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        chatbot = active_chatbots[request.session_id]
        response = await chatbot.chat(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

@app.post("/mcp/connect", response_model=InitializeResponse)
async def connect_to_mcp(request: MCPServerConnectRequest):
    """Connect to an MCP server"""
    try:
        session_id = request.session_id or generate_session_id()
        
        # Clean up existing session if it exists
        if session_id in active_clients:
            await cleanup_session(session_id)
        
        # Create MCP client
        client = await OllamaMCPPackage.create_client(model_name=request.model_name)
        
        # Connect to server based on type
        if request.server_type == "sse":
            if not request.server_url:
                raise HTTPException(status_code=400, detail="server_url is required for SSE connections")
            
            await client.connect_to_sse_server(server_url=request.server_url)
        
        elif request.server_type == "stdio":
            if not request.command or not request.args:
                raise HTTPException(status_code=400, detail="command and args are required for STDIO connections")
            
            await client.connect_to_stdio_server(command=request.command, args=request.args)
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported server type: {request.server_type}")
        
        # Store in active clients
        active_clients[session_id] = client
        
        return InitializeResponse(
            session_id=session_id,
            status="connected",
            model=request.model_name
        )
    except Exception as e:
        app_logger.error(f"Error connecting to MCP server: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error connecting to MCP server: {str(e)}")

@app.post("/mcp/query", response_model=ChatResponse)
async def process_mcp_query(request: ChatRequest):
    """Process a query with MCP tools"""
    if request.session_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        client = active_clients[request.session_id]
        
        # Process query
        response = await client.process_query(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing MCP query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing MCP query: {str(e)}")

@app.post("/mcp/direct-query", response_model=ChatResponse)
async def process_direct_query(request: ChatRequest):
    """Process a direct query with Ollama (no MCP tools)"""
    if request.session_id not in active_clients:
        raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
    
    try:
        client = active_clients[request.session_id]
        
        # Set direct mode
        client.direct_mode = True
        
        # Process direct query
        response = await client.process_direct_query(request.message)
        
        return ChatResponse(
            response=response,
            session_id=request.session_id
        )
    except Exception as e:
        app_logger.error(f"Error processing direct query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing direct query: {str(e)}")

@app.get("/available-models")
async def get_available_models():
    """Get list of available Ollama models"""
    try:
        models = await OllamaMCPPackage.get_available_models()
        return {"models": models}
    except Exception as e:
        app_logger.error(f"Error getting available models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting available models: {str(e)}")

@app.get("/mcp/servers")
async def get_mcp_servers():
    """Get list of configured MCP servers"""
    try:
        config = await OllamaMCPPackage.load_mcp_config()
        return {"servers": config.get("mcpServers", {})}
    except Exception as e:
        app_logger.error(f"Error getting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting MCP servers: {str(e)}")

@app.delete("/sessions/{session_id}", response_model=StatusResponse)
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """Delete a session"""
    if session_id not in active_clients and session_id not in active_chatbots:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    
    # Schedule cleanup to happen in the background
    background_tasks.add_task(cleanup_session, session_id)
    
    return StatusResponse(
        status="cleanup_scheduled",
        active_sessions=list(set(list(active_clients.keys()) + list(active_chatbots.keys()))),
        message=f"Session {session_id} scheduled for cleanup"
    )

@app.get("/sessions", response_model=StatusResponse)
async def get_sessions():
    """Get active sessions"""
    sessions = list(set(list(active_clients.keys()) + list(active_chatbots.keys())))
    return StatusResponse(
        status="ok",
        active_sessions=sessions
    )


# ----- Programmatic API Examples -----

async def example_standalone():
    """Example of using the package with standalone Ollama (no MCP)"""
    # Create a standalone chatbot
    chatbot = await OllamaMCPPackage.create_standalone_chatbot(
        model_name="llama3.2",
        system_message="You are a helpful assistant who speaks like a pirate.",
        temperature=0.8
    )
    
    try:
        # Chat with the model
        response = await chatbot.chat("Tell me about neural networks.")
        print(f"Chatbot: {response}")
        
        # Continue the conversation
        response = await chatbot.chat("Summarize what you just told me.")
        print(f"Chatbot: {response}")
    finally:
        # Clean up when done
        await chatbot.cleanup()

async def example_with_mcp():
    """Example of using the package with MCP tools"""
    # Create an MCP client
    client = await OllamaMCPPackage.create_client()
    
    try:
        # Connect to an SSE server
        await client.connect_to_sse_server("http://localhost:3000/sse")
        
        # Process a query
        response = await client.process_query("What's the weather in Paris?")
        print(f"Response: {response}")
    finally:
        # Clean up when done
        await client.cleanup()


# ----- Main Function -----

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    # Example: Run the FastAPI server
    start_server()    
    # Examples of programmatic usage are defined above
    # To run them directly:
    # asyncio.run(example_standalone())
    # asyncio.run(example_with_mcp())
