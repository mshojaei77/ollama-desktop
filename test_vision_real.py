import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from api.ollama_mcp_api import app

client = TestClient(app)

@pytest.mark.integration
def test_chat_vision_endpoint_real():
    # 1. Initialize a standalone chatbot session
    init_resp = client.post(
        "/chat/initialize",
        json={"model_name": "llama3.2"}
    )
    assert init_resp.status_code == 200, init_resp.text
    session_id = init_resp.json().get("session_id")
    assert session_id, "No session_id returned from initialization"

    # 2. Send vision chat with the sample image
    image_file = Path("api/sample.png")
    assert image_file.exists(), f"sample.png not found at {image_file}"
    png_bytes = image_file.read_bytes()
    files = [
        (
            'images',
            ('sample.png', png_bytes, 'image/png')
        ),
    ]
    data = {"session_id": session_id, "message": "Extract text from the image."}
    vis_resp = client.post(
        "/chat/vision",
        data=data,
        files=files
    )
    assert vis_resp.status_code == 200, vis_resp.text
    result = vis_resp.json().get("response", "")

    # 3. Check that expected OCR text appears in the response
    assert "Persian Jazz" in result, f"Expected 'Persian Jazz' in result, got: {result}"
    assert "Hits of the 80's" in result, f"Expected 'Hits of the 80's' in result, got: {result}"

    # Print output for manual inspection if needed
    print("Vision API result:\n", result) 