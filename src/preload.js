const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'api', {
    listModels: () => ipcRenderer.invoke('list-models'),
    initializeChat: (params) => ipcRenderer.invoke('initialize-chat', params),
    chat: (params) => ipcRenderer.invoke('chat', params),
    closeSession: (params) => ipcRenderer.invoke('close-session', params),
    connectMCP: (params) => ipcRenderer.invoke('connect-mcp', params),
    mcpQuery: (params) => ipcRenderer.invoke('mcp-query', params),
    directQuery: (params) => ipcRenderer.invoke('direct-query', params),
    getMCPServers: () => ipcRenderer.invoke('get-mcp-servers'),
    getSessions: () => ipcRenderer.invoke('get-sessions'),
    
    // New methods for saved sessions
    getSavedSessions: () => ipcRenderer.invoke('get-saved-sessions'),
    loadSession: (params) => ipcRenderer.invoke('load-session', params),
    togglePinSession: (params) => ipcRenderer.invoke('toggle-pin-session', params),
    saveSession: (params) => ipcRenderer.invoke('save-session', params)
  }
);