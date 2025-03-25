const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const axios = require('axios');

// Base URL for Ollama API
const OLLAMA_API_URL = 'http://localhost:11434/api';

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

// Handle IPC messages from renderer process

// List available models
ipcMain.handle('list-models', async () => {
  try {
    const response = await axios.get(`${OLLAMA_API_URL}/tags`);
    return response.data.models || [];
  } catch (error) {
    console.error('Error fetching models:', error);
    return { error: error.message };
  }
});

// Generate chat completion
ipcMain.handle('chat', async (_, { model, messages }) => {
  try {
    const response = await axios.post(`${OLLAMA_API_URL}/chat`, {
      model,
      messages,
      stream: false
    });
    return response.data;
  } catch (error) {
    console.error('Error in chat:', error);
    return { error: error.message };
  }
});

// Pull a model
ipcMain.handle('pull-model', async (_, { model }) => {
  try {
    const response = await axios.post(`${OLLAMA_API_URL}/pull`, {
      model,
      stream: false
    });
    return response.data;
  } catch (error) {
    console.error('Error pulling model:', error);
    return { error: error.message };
  }
});