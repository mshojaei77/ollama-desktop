const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

// Base URL for FastAPI server
const MCP_API_URL = 'http://localhost:8000';

// Store active sessions
const activeSessions = new Map();

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, '../preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, '../../assets/ollama.ico')
  });

  // Disable the menu bar
  mainWindow.setMenuBarVisibility(false);

  mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  
  // Open DevTools in development
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();
  
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

// Clean up all sessions when app is about to quit
app.on('before-quit', async () => {
  const cleanupPromises = [];
  for (const sessionId of activeSessions.keys()) {
    cleanupPromises.push(
      axios.delete(`${MCP_API_URL}/sessions/${sessionId}`)
        .catch(err => console.error(`Failed to clean up session ${sessionId}:`, err))
    );
  }
  await Promise.allSettled(cleanupPromises);
});

// Helper function for API requests
async function apiRequest(endpoint, method = "GET", data = null) {
  const url = `${MCP_API_URL}${endpoint}`;
  
  try {
    let response;
    
    if (method === "GET") {
      response = await axios.get(url);
    } else if (method === "POST") {
      response = await axios.post(url, data);
    } else if (method === "DELETE") {
      response = await axios.delete(url);
    }
    
    return response.data;
  } catch (error) {
    console.error(`API error (${endpoint}):`, error);
    throw error;
  }
}

// List available models - used for dropdown menu
ipcMain.handle('list-models', async () => {
  try {
    const response = await apiRequest('/available-models');
    return response.models || [];
  } catch (error) {
    console.error('Error fetching models:', error);
    return { error: error.message };
  }
});

// NEW HANDLER: List models sorted by last used time
ipcMain.handle('list-recent-models', async () => {
  try {
    // Use the new endpoint that sorts by last_used
    const response = await apiRequest('/models?sort_by=last_used');
    return response.models || [];
  } catch (error) {
    console.error('Error fetching recent models:', error);
    return { error: error.message };
  }
});

// Initialize a chat session
ipcMain.handle('initialize-chat', async (_, { model, systemMessage }) => {
  try {
    const data = {
      model_name: model,
      system_message: systemMessage
    };
    
    const response = await apiRequest('/chat/initialize', 'POST', data);
    
    const sessionId = response.session_id;
    activeSessions.set(sessionId, { 
      id: sessionId,
      type: 'standalone',
      model: response.model
    });
    
    return { 
      sessionId: sessionId,
      model: response.model,
      status: response.status
    };
  } catch (error) {
    console.error('Error initializing chat:', error);
    return { error: error.message };
  }
});

// Generate chat completion
ipcMain.handle('chat', async (_, { sessionId, message }) => {
  try {
    // Check if session exists
    if (!activeSessions.has(sessionId)) {
      return { error: 'Session not found. Please initialize a chat session first.' };
    }
    
    const data = {
      session_id: sessionId,
      message: message
    };
    
    const response = await apiRequest('/chat/message', 'POST', data);
    
    return {
      response: response.response,
      sessionId: response.session_id
    };
  } catch (error) {
    console.error('Error in chat:', error);
    return { error: error.message };
  }
});

// Connect to MCP server
ipcMain.handle('connect-mcp', async (_, { model, serverType, serverUrl, command, args }) => {
  try {
    const data = {
      model_name: model,
      server_type: serverType.toLowerCase(),
      server_url: serverUrl,
      command: command,
      args: args
    };
    
    const response = await apiRequest('/mcp/connect', 'POST', data);
    
    const sessionId = response.session_id;
    activeSessions.set(sessionId, { 
      id: sessionId,
      type: 'mcp',
      model: response.model,
      serverType: serverType
    });
    
    return { 
      sessionId: sessionId,
      model: response.model,
      status: response.status
    };
  } catch (error) {
    console.error('Error connecting to MCP server:', error);
    return { error: error.message };
  }
});

// Process MCP query
ipcMain.handle('mcp-query', async (_, { sessionId, message }) => {
  try {
    if (!activeSessions.has(sessionId)) {
      return { error: 'Session not found. Please connect to an MCP server first.' };
    }
    
    const data = {
      session_id: sessionId,
      message: message
    };
    
    const response = await apiRequest('/mcp/query', 'POST', data);
    
    return {
      response: response.response,
      sessionId: response.session_id
    };
  } catch (error) {
    console.error('Error in MCP query:', error);
    return { error: error.message };
  }
});

// Process direct query (no MCP tools)
ipcMain.handle('direct-query', async (_, { sessionId, message }) => {
  try {
    if (!activeSessions.has(sessionId)) {
      return { error: 'Session not found. Please connect to an MCP server first.' };
    }
    
    const data = {
      session_id: sessionId,
      message: message
    };
    
    const response = await apiRequest('/mcp/direct-query', 'POST', data);
    
    return {
      response: response.response,
      sessionId: response.session_id
    };
  } catch (error) {
    console.error('Error in direct query:', error);
    return { error: error.message };
  }
});

// Get available MCP servers
ipcMain.handle('get-mcp-servers', async () => {
  try {
    const response = await apiRequest('/mcp/servers');
    return response.servers || {};
  } catch (error) {
    console.error('Error fetching MCP servers:', error);
    return { error: error.message };
  }
});

// Get active sessions
ipcMain.handle('get-sessions', async () => {
  try {
    const response = await apiRequest('/sessions');
    return response.active_sessions || [];
  } catch (error) {
    console.error('Error fetching sessions:', error);
    return { error: error.message };
  }
});

// Close a session
ipcMain.handle('close-session', async (_, { sessionId }) => {
  try {
    if (!activeSessions.has(sessionId)) {
      return { status: 'error', message: 'Session not found' };
    }
    
    const response = await apiRequest(`/sessions/${sessionId}`, 'DELETE');
    activeSessions.delete(sessionId);
    
    return { 
      status: response.status,
      message: response.message || 'Session closed successfully'
    };
  } catch (error) {
    console.error('Error closing session:', error);
    return { error: error.message };
  }
});

// Get saved sessions
ipcMain.handle('get-saved-sessions', async () => {
  try {
    const response = await apiRequest('/sessions/saved');
    return response || [];
  } catch (error) {
    console.error('Error fetching saved sessions:', error);
    return { error: error.message };
  }
});

// Load a saved session
ipcMain.handle('load-session', async (_, { sessionId }) => {
  try {
    const response = await apiRequest(`/sessions/load/${sessionId}`, 'GET');
    
    if (response.session_type === 'standalone') {
      activeSessions.set(sessionId, {
        id: sessionId,
        type: 'standalone',
        model: response.model
      });
    } else if (response.session_type === 'mcp') {
      activeSessions.set(sessionId, {
        id: sessionId,
        type: 'mcp',
        model: response.model,
        serverType: response.server_type
      });
    }
    
    return {
      sessionId: response.session_id,
      messages: response.messages,
      status: response.status,
      model: response.model
    };
  } catch (error) {
    console.error('Error loading session:', error);
    return { error: error.message };
  }
});

// Toggle pin status for a session
ipcMain.handle('toggle-pin-session', async (_, { sessionId }) => {
  try {
    const response = await apiRequest(`/sessions/pin/${sessionId}`, 'PUT');
    return {
      sessionId: response.session_id,
      pinned: response.pinned
    };
  } catch (error) {
    console.error('Error toggling pin status:', error);
    return { error: error.message };
  }
});

// Save a session
ipcMain.handle('save-session', async (_, { sessionId }) => {
  try {
    const data = {
      session_id: sessionId,
      message: ""  // Empty message as we're just saving the session
    };
    
    const response = await apiRequest('/sessions/save', 'POST', data);
    return {
      sessionId: response.session_id,
      status: response.status,
      title: response.title
    };
  } catch (error) {
    console.error('Error saving session:', error);
    return { error: error.message };
  }
});