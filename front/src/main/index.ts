import { app, shell, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import axios from 'axios'

// Track API server process
let apiServerProcess: any = null

async function cleanupProcesses() {
  try {
    // Send cleanup request to API server
    await axios.post('http://localhost:8000/cleanup')
    console.log('Sent cleanup request to API server')

    // Wait a moment for the API server to clean up
    await new Promise(resolve => setTimeout(resolve, 1000))

    // Try to check if API server is still responding
    try {
      await axios.get('http://localhost:8000/')
    } catch (error) {
      // If we get an error, it means the server is no longer running (good)
      console.log('API server successfully terminated')
      return
    }

    // If we reach here, server is still running, wait a bit longer
    await new Promise(resolve => setTimeout(resolve, 2000))

  } catch (error) {
    console.error('Error sending cleanup request:', error)
  }
}

function createWindow(): void {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 1280,
    height: 900,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      // Always enable web security even in development
      webSecurity: true,
      // Disable insecure content
      allowRunningInsecureContent: false
    }
  })
  // Only open DevTools in development mode
  if (is.dev) {
    mainWindow.webContents.openDevTools()
  }

  // Set CSP headers with proper security configurations
  mainWindow.webContents.session.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        'Content-Security-Policy': "default-src 'self'; connect-src 'self' http://localhost:8000; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; style-src-elem 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https://via.placeholder.com https://res.cloudinary.com;"
      }
    })
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // HMR for renderer base on electron-vite cli.
  // Load the remote URL for development or the local html file for production.
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }

  // Handle window close event
  mainWindow.on('close', async (e) => {
    if (mainWindow.isClosable()) {
      e.preventDefault() // Prevent the window from closing immediately
      
      try {
        await cleanupProcesses()
        console.log('Cleanup completed')
        app.exit(0) // Exit the app after cleanup
      } catch (error) {
        console.error('Error during cleanup:', error)
        app.exit(1) // Exit with error code
      }
    }
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.whenReady().then(() => {
  // Set app user model id for windows
  electronApp.setAppUserModelId('com.electron')

  // Default open or close DevTools by F12 in development
  // and ignore CommandOrControl + R in production.
  // see https://github.com/alex8088/electron-toolkit/tree/master/packages/utils
  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // IPC test
  ipcMain.on('ping', () => console.log('pong'))

  createWindow()

  app.on('activate', function () {
    // On macOS it's common to re-create a window in the app when the
    // dock icon is clicked and there are no other windows open.
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', async () => {
  try {
    await cleanupProcesses()
  } catch (error) {
    console.error('Error during final cleanup:', error)
  }
  
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.
