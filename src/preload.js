const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld(
  'api', {
    listModels: () => ipcRenderer.invoke('list-models'),
    chat: (params) => ipcRenderer.invoke('chat', params),
    pullModel: (params) => ipcRenderer.invoke('pull-model', params)
  }
);