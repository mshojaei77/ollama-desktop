import subprocess
import sys
import uvicorn
from fastapi import FastAPI
from app.core.chatbot import app_logger

def start_frontend():
    """Start the frontend development server in a separate terminal"""
    try:
        frontend_cmd = "cd front && npm run dev"
        
        if sys.platform.startswith('win'):
            # Windows: run without showing command prompt
            subprocess.Popen(frontend_cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        elif sys.platform.startswith('darwin'):
            # macOS: run in background
            subprocess.Popen(['bash', '-c', frontend_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # Linux: run in background
            subprocess.Popen(['bash', '-c', frontend_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
        app_logger.info("Started frontend development server in background")
    except Exception as e:
        app_logger.error(f"Failed to start frontend: {str(e)}")

def start_server(app: FastAPI):
    """Start the FastAPI server"""
    uvicorn.run(app, host="0.0.0.0", port=8000)