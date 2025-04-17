import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from api.ollama_mcp_api import app, active_chatbots, db


class DummyChatbot:
    def __init__(self):
        self.called = False
        self.last_message = None
        self.last_image_paths = None

    async def chat_with_image(self, message: str, image_paths: list):
        self.called = True
        self.last_message = message
        self.last_image_paths = image_paths
        return "dummy vision response"


@pytest.fixture(autouse=True)
def vision_session(monkeypatch):
    # Prepare a dummy session and chatbot
    session_id = "vision-test-session"
    dummy = DummyChatbot()
    active_chatbots[session_id] = dummy

    # Patch database hooks to async no-op coroutines
    async def fake_add_chat_message(*args, **kwargs):
        return None
    async def fake_update_session_activity(*args, **kwargs):
        return None
    monkeypatch.setattr(db, "add_chat_message", fake_add_chat_message)
    monkeypatch.setattr(db, "update_session_activity", fake_update_session_activity)

    yield session_id, dummy

    # Cleanup after test
    active_chatbots.pop(session_id, None)


def test_chat_vision_endpoint(vision_session):
    session_id, dummy = vision_session
    client = TestClient(app)

    # Prepare multipart form data
    data = {
        'session_id': session_id,
        'message': 'Hello Vision'
    }
    # Use existing sample.png from the api folder
    png_bytes = Path('api/sample.png').read_bytes()
    files = [
        ('images', ('sample.png', png_bytes, 'image/png')),
    ]

    response = client.post("/chat/vision", data=data, files=files)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data == {"response": "dummy vision response", "session_id": session_id}

    # Verify that the dummy chatbot was called correctly
    assert dummy.called is True
    assert dummy.last_message == 'Hello Vision'
    # Verify that one image path was passed and filename matches
    assert dummy.last_image_paths is not None
    assert len(dummy.last_image_paths) == 1
    assert Path(dummy.last_image_paths[0]).name == "sample.png"

