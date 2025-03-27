import streamlit as st
import requests
import json
import time
import pandas as pd
from typing import Dict, List, Optional, Any, Union

# Set page configuration
st.set_page_config(
    page_title="Ollama MCP Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8000"

# Helper functions to interact with API
def api_request(endpoint, method="GET", data=None):
    """Make requests to the Ollama MCP API"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API error: {str(e)}")
        return None

def get_available_models():
    """Get list of available models from API"""
    response = api_request("/available-models")
    if response:
        return response.get("models", [])
    return []

def get_mcp_servers():
    """Get list of configured MCP servers"""
    response = api_request("/mcp/servers")
    if response:
        return response.get("servers", {})
    return {}

def initialize_chatbot(model_name, system_message=None, session_id=None):
    """Initialize a standalone chatbot"""
    data = {
        "model_name": model_name,
        "system_message": system_message,
        "session_id": session_id
    }
    return api_request("/chat/initialize", method="POST", data=data)

def send_chat_message(session_id, message):
    """Send a message to a chatbot"""
    data = {
        "session_id": session_id,
        "message": message
    }
    return api_request("/chat/message", method="POST", data=data)

def connect_to_mcp(server_type, model_name, session_id=None, server_url=None, command=None, args=None):
    """Connect to an MCP server"""
    data = {
        "server_type": server_type,
        "model_name": model_name,
        "session_id": session_id,
        "server_url": server_url,
        "command": command,
        "args": args
    }
    return api_request("/mcp/connect", method="POST", data=data)

def process_mcp_query(session_id, message):
    """Process a query with MCP tools"""
    data = {
        "session_id": session_id,
        "message": message
    }
    return api_request("/mcp/query", method="POST", data=data)

def process_direct_query(session_id, message):
    """Process a direct query without MCP tools"""
    data = {
        "session_id": session_id,
        "message": message
    }
    return api_request("/mcp/direct-query", method="POST", data=data)

def delete_session(session_id):
    """Delete a session"""
    return api_request(f"/sessions/{session_id}", method="DELETE")

def get_active_sessions():
    """Get active sessions"""
    response = api_request("/sessions")
    if response:
        return response.get("active_sessions", [])
    return []

# Initialize session state if not already done
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = {}  # session_id -> list of (role, message) tuples

if 'active_sessions' not in st.session_state:
    st.session_state.active_sessions = {}  # session_id -> session info

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

# UI Components
st.title("🤖 Ollama MCP Demo")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Refresh models
    if st.button("Refresh Available Models"):
        models = get_available_models()
        st.session_state.models = models
    
    # Get models (first time or after refresh)
    if 'models' not in st.session_state:
        models = get_available_models()
        st.session_state.models = models
    
    # Model selection
    selected_model = st.selectbox(
        "Select Model",
        options=st.session_state.models,
        index=0 if st.session_state.models else None
    )
    
    # Get MCP servers
    if st.button("Refresh MCP Servers"):
        mcp_servers = get_mcp_servers()
        st.session_state.mcp_servers = mcp_servers
    
    # List MCP servers (first time or after refresh)
    if 'mcp_servers' not in st.session_state:
        mcp_servers = get_mcp_servers()
        st.session_state.mcp_servers = mcp_servers
    
    # Display active sessions
    st.header("Active Sessions")
    
    # Button to refresh active sessions
    if st.button("Refresh Sessions"):
        sessions = get_active_sessions()
        # Update session state with the latest info
        for session_id in sessions:
            if session_id not in st.session_state.active_sessions:
                st.session_state.active_sessions[session_id] = {"id": session_id, "type": "unknown"}
    
    # Display and allow selection of active sessions
    for session_id, session_info in st.session_state.active_sessions.items():
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button(f"Select: {session_id[:10]}...", key=f"sel_{session_id}"):
                st.session_state.current_session = session_id
        with col2:
            if st.button("🗑️", key=f"del_{session_id}"):
                delete_session(session_id)
                if session_id in st.session_state.active_sessions:
                    del st.session_state.active_sessions[session_id]
                if session_id == st.session_state.current_session:
                    st.session_state.current_session = None
                st.experimental_rerun()

# Main content area with tabs
tab1, tab2, tab3 = st.tabs(["Standalone Chatbot", "MCP Connection", "Session Management"])

# Tab 1: Standalone Chatbot
with tab1:
    st.header("Standalone Ollama Chatbot")
    
    with st.expander("Initialize New Chatbot", expanded=True if not st.session_state.current_session else False):
        system_message = st.text_area(
            "System Message (Optional)",
            value="You are a helpful assistant.",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Initialize Chatbot", use_container_width=True):
                with st.spinner("Initializing chatbot..."):
                    response = initialize_chatbot(selected_model, system_message)
                    if response:
                        session_id = response["session_id"]
                        st.session_state.active_sessions[session_id] = {
                            "id": session_id,
                            "type": "standalone",
                            "model": response["model"]
                        }
                        st.session_state.current_session = session_id
                        st.session_state.chat_history[session_id] = []
                        st.success(f"Chatbot initialized with session ID: {session_id}")
                        st.experimental_rerun()
    
    # Chat interface (if a session is selected)
    if st.session_state.current_session:
        session_id = st.session_state.current_session
        session_info = st.session_state.active_sessions.get(session_id, {})
        
        # Only show chat for standalone chatbots in this tab
        if session_info.get("type") == "standalone":
            st.subheader(f"Chat with {session_info.get('model', 'Model')}")
            
            # Display chat history
            for i, (role, message) in enumerate(st.session_state.chat_history.get(session_id, [])):
                if role == "user":
                    st.chat_message("user").write(message)
                else:
                    st.chat_message("assistant").write(message)
            
            # Chat input
            user_input = st.chat_input("Type your message here...")
            if user_input:
                # Add user message to chat history
                if session_id not in st.session_state.chat_history:
                    st.session_state.chat_history[session_id] = []
                st.session_state.chat_history[session_id].append(("user", user_input))
                
                # Display user message
                st.chat_message("user").write(user_input)
                
                # Get response from API
                with st.spinner("Thinking..."):
                    response = send_chat_message(session_id, user_input)
                    if response:
                        bot_response = response["response"]
                        # Add bot response to chat history
                        st.session_state.chat_history[session_id].append(("assistant", bot_response))
                        # Display bot response
                        st.chat_message("assistant").write(bot_response)

# Tab 2: MCP Connection
with tab2:
    st.header("MCP Tools Connection")
    
    with st.expander("Connect to MCP Server", expanded=True if not st.session_state.current_session else False):
        server_type = st.radio("Server Type", ["SSE", "STDIO"])
        
        if server_type == "SSE":
            server_url = st.text_input("Server URL", value="http://localhost:3000/sse")
            command = None
            args = None
        else:  # STDIO
            server_url = None
            command = st.text_input("Command", value="python")
            args_input = st.text_input("Arguments (comma-separated)", value="-m mcp.server")
            args = [arg.strip() for arg in args_input.split(",")] if args_input else []
        
        if st.button("Connect to MCP Server"):
            with st.spinner("Connecting to MCP server..."):
                response = connect_to_mcp(
                    server_type.lower(),
                    selected_model,
                    server_url=server_url,
                    command=command,
                    args=args
                )
                if response:
                    session_id = response["session_id"]
                    st.session_state.active_sessions[session_id] = {
                        "id": session_id,
                        "type": "mcp",
                        "model": response["model"],
                        "server_type": server_type
                    }
                    st.session_state.current_session = session_id
                    st.session_state.chat_history[session_id] = []
                    st.success(f"Connected to MCP server with session ID: {session_id}")
                    st.experimental_rerun()
    
    # Chat interface for MCP (if a session is selected)
    if st.session_state.current_session:
        session_id = st.session_state.current_session
        session_info = st.session_state.active_sessions.get(session_id, {})
        
        # Only show chat for MCP connections in this tab
        if session_info.get("type") == "mcp":
            st.subheader(f"MCP Chat with {session_info.get('model', 'Model')}")
            
            # Query type selector
            query_type = st.radio("Query Type", ["MCP Tools", "Direct (No Tools)"])
            
            # Display chat history
            for i, (role, message) in enumerate(st.session_state.chat_history.get(session_id, [])):
                if role == "user":
                    st.chat_message("user").write(message)
                else:
                    st.chat_message("assistant").write(message)
            
            # Chat input
            user_input = st.chat_input("Type your message here...")
            if user_input:
                # Add user message to chat history
                if session_id not in st.session_state.chat_history:
                    st.session_state.chat_history[session_id] = []
                st.session_state.chat_history[session_id].append(("user", user_input))
                
                # Display user message
                st.chat_message("user").write(user_input)
                
                # Process based on query type
                with st.spinner("Processing..."):
                    if query_type == "MCP Tools":
                        response = process_mcp_query(session_id, user_input)
                    else:  # Direct
                        response = process_direct_query(session_id, user_input)
                    
                    if response:
                        bot_response = response["response"]
                        # Add bot response to chat history
                        st.session_state.chat_history[session_id].append(("assistant", bot_response))
                        # Display bot response
                        st.chat_message("assistant").write(bot_response)

# Tab 3: Session Management
with tab3:
    st.header("Session Management")
    
    # Display all active sessions from API
    if st.button("Refresh All Sessions from API"):
        sessions = get_active_sessions()
        # Update our local state with API state
        st.session_state.active_sessions_api = sessions
    
    # Show sessions and allow deletion
    if hasattr(st.session_state, 'active_sessions_api'):
        st.subheader("All Active Sessions (from API)")
        
        if not st.session_state.active_sessions_api:
            st.info("No active sessions found.")
        else:
            for session_id in st.session_state.active_sessions_api:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(session_id)
                with col2:
                    if st.button("Delete", key=f"api_del_{session_id}"):
                        delete_session(session_id)
                        st.success(f"Session {session_id} deleted")
                        st.session_state.active_sessions_api.remove(session_id)
                        if session_id in st.session_state.active_sessions:
                            del st.session_state.active_sessions[session_id]
                        if session_id == st.session_state.current_session:
                            st.session_state.current_session = None
    
    # Clear local session state
    if st.button("Clear Local Session State"):
        st.session_state.active_sessions = {}
        st.session_state.chat_history = {}
        st.session_state.current_session = None
        st.success("Local session state cleared")

# Footer
st.markdown("---")
st.markdown("### Ollama MCP API Demo")
st.markdown("This demo showcases the capabilities of the Ollama MCP API, allowing interaction with both standalone chatbots and MCP-enabled tools.")