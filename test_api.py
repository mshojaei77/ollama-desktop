import requests
import json
import os

# API base URL
BASE_URL = "http://localhost:8000"

def initialize_session():
    """Initialize a new chatbot session and return the session ID"""
    url = f"{BASE_URL}/chat/initialize"
    payload = {
        "model_name": "llama3.2",
        "system_message": "You are an AI assistant specialized in machine learning."
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        session_id = data["session_id"]
        print(f"Session initialized successfully. Session ID: {session_id}")
        return session_id
    else:
        print(f"Failed to initialize session: {response.status_code} - {response.text}")
        return None

def upload_file(session_id, file_path):
    """Upload a file to add context to a session"""
    url = f"{BASE_URL}/sessions/{session_id}/upload_file"
    
    with open(file_path, 'rb') as file:
        files = {'file': (os.path.basename(file_path), file, 'text/plain')}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        print(f"File uploaded successfully: {response.json()}")
        return True
    else:
        print(f"Failed to upload file: {response.status_code} - {response.text}")
        return False

def send_message(session_id, message):
    """Send a message to the chatbot and get a response"""
    url = f"{BASE_URL}/chat/message"
    payload = {
        "message": message,
        "session_id": session_id
    }
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data['response']}")
        return data['response']
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")
        return None

# Main test flow
def main():
    # Step 1: Initialize a session
    session_id = initialize_session()
    if not session_id:
        return
    
    # Step 2: Upload the sample.md file
    file_path = "sample.md"
    if not upload_file(session_id, file_path):
        return
    
    # Step 3: Send a message that should use context from the uploaded file
    print("\nSending message without context reference...")
    send_message(session_id, "Tell me about machine learning.")
    
    # Step 4: Send a message that should specifically use context from the uploaded file
    print("\nSending message with context reference...")
    send_message(session_id, "What are the types of machine learning mentioned in the document?")
    
    # Step 5: Test with a specific question about something in the document
    print("\nSending specific question about the document...")
    send_message(session_id, "What are the key innovations behind LLMs according to the document?")

if __name__ == "__main__":
    main() 