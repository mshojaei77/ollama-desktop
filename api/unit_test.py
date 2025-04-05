import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add the project directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ollama_mcp_api import app, active_clients, active_chatbots

# Create a TestClient for testing the API
client = TestClient(app)

# Mock classes and functions
class MockChatbot:
    def __init__(self, model_name, system_message=None):
        self.model_name = model_name
        self.system_message = system_message
        self.chat = AsyncMock(return_value="Mock chatbot response")
        self.cleanup = AsyncMock()

class MockMCPClient:
    def __init__(self, model_name):
        self.model_name = model_name
        self.connect_to_sse_server = AsyncMock()
        self.connect_to_stdio_server = AsyncMock()
        self.process_query = AsyncMock(return_value="Mock MCP response")
        self.process_direct_query = AsyncMock(return_value="Mock direct query response")
        self.cleanup = AsyncMock()
        self.direct_mode = False

# Mock database functions
@pytest.fixture
def mock_db():
    with patch("ollama_mcp_api.db") as mock_db:
        mock_db.init_db = MagicMock()
        mock_db.migrate_database = MagicMock()
        mock_db.create_session = AsyncMock()
        mock_db.add_chat_message = AsyncMock()
        mock_db.update_session_activity = AsyncMock()
        mock_db.deactivate_session = AsyncMock()
        mock_db.get_active_sessions = AsyncMock(return_value=[{"session_id": "test-session-1"}])
        mock_db.get_session = AsyncMock(return_value={"session_id": "test-session-1"})
        mock_db.get_filtered_chat_history = AsyncMock(return_value=[
            {"role": "user", "message": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "message": "Hi there!", "timestamp": "2023-01-01T00:00:01"}
        ])
        mock_db.get_chat_history = AsyncMock(return_value=[
            {"role": "user", "content": "Hello", "timestamp": "2023-01-01T00:00:00"},
            {"role": "assistant", "content": "Hi there!", "timestamp": "2023-01-01T00:00:01"}
        ])
        mock_db.get_recently_used_models = AsyncMock(return_value=[
            {"name": "llama3.2", "last_used": "2023-01-01T00:00:00"}
        ])
        mock_db.get_models = AsyncMock(return_value=[
            {"name": "llama3.2", "last_used": "2023-01-01T00:00:00"},
            {"name": "gemma", "last_used": "2023-01-01T00:00:01"}
        ])
        mock_db.ensure_model_exists = AsyncMock()
        mock_db.get_sessions_with_message_count = AsyncMock(return_value=[
            {
                "session_id": "test-session-1",
                "model_name": "llama3.2",
                "session_type": "chatbot",
                "system_message": "You are a helpful assistant",
                "created_at": "2023-01-01T00:00:00",
                "last_active": "2023-01-01T00:00:02",
                "is_active": True,
                "message_count": 2,
                "first_message_time": "2023-01-01T00:00:00",
                "last_message_time": "2023-01-01T00:00:01"
            }
        ])
        mock_db.search_chats = AsyncMock(return_value=[
            {
                "session_id": "test-session-1",
                "model_name": "llama3.2",
                "session_type": "chatbot",
                "system_message": "You are a helpful assistant",
                "created_at": "2023-01-01T00:00:00",
                "last_active": "2023-01-01T00:00:02",
                "is_active": True,
                "message_count": 2,
                "first_message_time": "2023-01-01T00:00:00",
                "last_message_time": "2023-01-01T00:00:01"
            }
        ])
        yield mock_db

# Mock OllamaMCPPackage
@pytest.fixture
def mock_ollama_mcp_package():
    with patch("ollama_mcp_api.OllamaMCPPackage") as mock_package:
        # Setup mock methods for the package
        mock_package.create_standalone_chatbot = AsyncMock(side_effect=lambda **kwargs: MockChatbot(**kwargs))
        mock_package.create_client = AsyncMock(side_effect=lambda **kwargs: MockMCPClient(**kwargs))
        mock_package.get_available_models = AsyncMock(return_value=["llama3.2", "gemma", "llama-3-8b"])
        mock_package.load_mcp_config = AsyncMock(return_value={
            "mcpServers": {
                "server1": {"type": "sse", "url": "http://localhost:3000/sse"},
                "server2": {"type": "stdio", "command": "python", "args": ["server.py"]}
            }
        })
        mock_package.save_mcp_config = AsyncMock(return_value=True)
        yield mock_package

# Clear global state between tests
@pytest.fixture(autouse=True)
def clear_globals():
    active_clients.clear()
    active_chatbots.clear()
    yield

# Tests
def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Ollama MCP API"
    assert "active_sessions" in data

def test_initialize_chatbot(mock_ollama_mcp_package, mock_db):
    """Test chatbot initialization."""
    response = client.post("/chat/initialize", json={
        "model_name": "llama3.2",
        "system_message": "You are a helpful assistant."
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["model"] == "llama3.2"
    assert "session_id" in data
    
    # Verify the mocks were called correctly
    mock_ollama_mcp_package.create_standalone_chatbot.assert_called_once()
    mock_db.create_session.assert_called_once()

def test_initialize_chatbot_empty_model(mock_ollama_mcp_package, mock_db):
    """Test chatbot initialization with empty model name."""
    response = client.post("/chat/initialize", json={
        "model_name": "",
        "system_message": "You are a helpful assistant."
    })
    assert response.status_code == 400
    assert "Model name cannot be empty" in response.json()["detail"]

def test_chat_message(mock_ollama_mcp_package, mock_db):
    """Test sending a message to a chatbot."""
    # First initialize a chatbot
    init_response = client.post("/chat/initialize", json={
        "model_name": "llama3.2",
        "system_message": "You are a helpful assistant."
    })
    session_id = init_response.json()["session_id"]
    
    # Send a message
    response = client.post("/chat/message", json={
        "message": "Hello, how are you?",
        "session_id": session_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Mock chatbot response"
    assert data["session_id"] == session_id
    
    # Verify mocks were called correctly
    mock_db.add_chat_message.assert_called()
    mock_db.update_session_activity.assert_called_once()

def test_chat_message_session_not_found(mock_db):
    """Test sending a message to a non-existent chatbot session."""
    response = client.post("/chat/message", json={
        "message": "Hello, how are you?",
        "session_id": "non-existent-session"
    })
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_mcp_connect(mock_ollama_mcp_package, mock_db):
    """Test connecting to an MCP server."""
    # Test SSE connection
    response = client.post("/mcp/connect", json={
        "server_type": "sse",
        "server_url": "http://localhost:3000/sse",
        "model_name": "llama3.2"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["model"] == "llama3.2"
    assert "session_id" in data
    
    # Verify mocks were called correctly
    mock_ollama_mcp_package.create_client.assert_called()
    mock_db.create_session.assert_called()

def test_mcp_connect_missing_url(mock_ollama_mcp_package):
    """Test connecting to an SSE server without URL."""
    response = client.post("/mcp/connect", json={
        "server_type": "sse",
        "model_name": "llama3.2"
    })
    assert response.status_code == 400
    assert "server_url is required" in response.json()["detail"]

def test_mcp_connect_stdio(mock_ollama_mcp_package, mock_db):
    """Test connecting to a STDIO server."""
    response = client.post("/mcp/connect", json={
        "server_type": "stdio",
        "command": "python",
        "args": ["server.py"],
        "model_name": "llama3.2"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "connected"
    assert data["model"] == "llama3.2"
    assert "session_id" in data

def test_mcp_query(mock_ollama_mcp_package, mock_db):
    """Test sending a query to an MCP client."""
    # First connect to an MCP server
    init_response = client.post("/mcp/connect", json={
        "server_type": "sse",
        "server_url": "http://localhost:3000/sse",
        "model_name": "llama3.2"
    })
    session_id = init_response.json()["session_id"]
    
    # Send a query
    response = client.post("/mcp/query", json={
        "message": "What's the weather in Paris?",
        "session_id": session_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Mock MCP response"
    assert data["session_id"] == session_id

def test_direct_query(mock_ollama_mcp_package, mock_db):
    """Test sending a direct query to an MCP client."""
    # First connect to an MCP server
    init_response = client.post("/mcp/connect", json={
        "server_type": "sse",
        "server_url": "http://localhost:3000/sse",
        "model_name": "llama3.2"
    })
    session_id = init_response.json()["session_id"]
    
    # Send a direct query
    response = client.post("/mcp/direct-query", json={
        "message": "Tell me about neural networks",
        "session_id": session_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Mock direct query response"
    assert data["session_id"] == session_id

def test_available_models(mock_ollama_mcp_package):
    """Test getting available models."""
    response = client.get("/available-models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 3
    assert "llama3.2" in data["models"]

def test_mcp_servers(mock_ollama_mcp_package):
    """Test getting MCP servers configuration."""
    response = client.get("/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert len(data["servers"]) == 2
    assert "server1" in data["servers"]
    assert "server2" in data["servers"]

def test_delete_session(mock_db):
    """Test deleting a session."""
    # First initialize a chatbot
    init_response = client.post("/chat/initialize", json={
        "model_name": "llama3.2",
        "system_message": "You are a helpful assistant."
    })
    session_id = init_response.json()["session_id"]
    
    # Delete the session
    response = client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cleanup_scheduled"
    assert "active_sessions" in data
    
    # Verify mock was called
    mock_db.deactivate_session.assert_called_once()

def test_delete_session_not_found(mock_db):
    """Test deleting a non-existent session."""
    response = client.delete("/sessions/non-existent-session")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_get_sessions(mock_db):
    """Test getting active sessions."""
    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert "active_sessions" in data
    assert len(data["active_sessions"]) == 1
    assert data["active_sessions"][0] == "test-session-1"

def test_get_chat_history(mock_db):
    """Test getting chat history for a session."""
    response = client.get("/chat/history/test-session-1")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "test-session-1"
    assert "history" in data
    assert len(data["history"]) == 2
    assert data["history"][0]["role"] == "user"
    assert data["history"][1]["role"] == "assistant"

def test_get_chat_history_not_found(mock_db):
    """Test getting chat history for a non-existent session."""
    # Override the default mock behavior just for this test
    mock_db.get_session.return_value = None
    
    response = client.get("/chat/history/non-existent-session")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_get_recent_models(mock_db):
    """Test getting recently used models."""
    response = client.get("/models/recent")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 1
    assert data["models"][0]["name"] == "llama3.2"

def test_get_models(mock_db):
    """Test getting all models."""
    response = client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 2
    assert data["models"][0]["name"] == "llama3.2"
    assert data["models"][1]["name"] == "gemma"

def test_get_models_with_sort(mock_db):
    """Test getting models with sorting."""
    response = client.get("/models?sort_by=last_used")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) == 2

def test_add_mcp_server(mock_ollama_mcp_package):
    """Test adding a new MCP server."""
    # Mock the write_ollama_config function
    with patch("ollama_mcp_api.write_ollama_config", AsyncMock(return_value=True)):
        # Test adding an SSE server
        response = client.post("/mcp/servers/add", json={
            "server_name": "test_server",
            "server_type": "sse",
            "server_url": "http://localhost:8080/sse"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "message" in data
        assert "test_server" in data["message"]
        
        # Verify the mocks were called correctly
        mock_ollama_mcp_package.load_mcp_config.assert_called()
        
        # Test adding an STDIO server
        response = client.post("/mcp/servers/add", json={
            "server_name": "stdio_server",
            "server_type": "stdio",
            "command": "python",
            "args": ["mcp_server.py"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "servers" in data
        assert "message" in data
        assert "stdio_server" in data["message"]

def test_add_mcp_server_validation(mock_ollama_mcp_package):
    """Test validation for adding MCP servers."""
    # Test missing server_name (this should be a validation error)
    response = client.post("/mcp/servers/add", json={
        "server_type": "sse",
        "server_url": "http://localhost:8080/sse"
    })
    assert response.status_code == 422  # Validation error
    
    # Test invalid server_type
    with patch("ollama_mcp_api.write_ollama_config", AsyncMock(return_value=True)):
        response = client.post("/mcp/servers/add", json={
            "server_name": "invalid_server",
            "server_type": "invalid",
            "server_url": "http://localhost:8080/sse"
        })
        assert response.status_code == 400
        assert "Unsupported server type" in response.json()["detail"]
        
        # Test missing server_url for SSE type
        response = client.post("/mcp/servers/add", json={
            "server_name": "missing_url",
            "server_type": "sse"
        })
        assert response.status_code == 400
        assert "server_url is required" in response.json()["detail"]
        
        # Test missing command for STDIO type
        response = client.post("/mcp/servers/add", json={
            "server_name": "missing_command",
            "server_type": "stdio"
        })
        assert response.status_code == 400
        assert "command is required" in response.json()["detail"]

def test_get_chats(mock_db):
    """Test getting all chats."""
    response = client.get("/chats")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "count" in data
    assert data["count"] == 1
    assert data["sessions"][0]["session_id"] == "test-session-1"
    assert data["sessions"][0]["model_name"] == "llama3.2"

def test_search_chats(mock_db):
    """Test searching for chats."""
    response = client.get("/chats/search?q=test")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert "count" in data
    assert data["count"] == 1
    assert data["sessions"][0]["session_id"] == "test-session-1"

if __name__ == "__main__":
    pytest.main(["-v", "api/unit_test.py"])
