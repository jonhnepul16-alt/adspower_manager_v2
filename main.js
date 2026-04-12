const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 850,
    backgroundColor: '#0f172a', // Matches the SaaS theme
    title: 'AdsPower Manager Pro',
    icon: path.join(__dirname, 'frontend/public/logo2_cropped.png'),
    frame: false, // Frameless window
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.removeMenu(); // Remove default menu bar

  // In development, load from Vite dev server
  // In production, load the built index.html
  const isDev = !app.isPackaged;
  if (isDev) {
    mainWindow.loadURL('http://localhost:8080');
    // Open DevTools in development
    // mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, 'frontend/dist/index.html'));
  }

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

function startBackend() {
  const isDev = !app.isPackaged;
  if (isDev) {
    console.log('Skipping backend spawn: concurrently handles it in dev mode.');
    return;
  }
  
  console.log('Starting Python backend (Production Mode)...');
  
  // O executável gerado pelo PyInstaller vai estar na pasta resources após o empacotamento com o electron-builder
  // Se configurado corretamente no package.json em "extraResources"
  const backendExe = path.join(process.resourcesPath, 'backend.exe');

  if (require('fs').existsSync(backendExe)) {
      console.log('Found packaged backend.exe at:', backendExe);
      pythonProcess = spawn(backendExe, [], {
          env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
      });
  } else {
      console.error('Packaged backend.exe NOT FOUND at:', backendExe);
  }

  if (pythonProcess) {
    pythonProcess.stdout.on('data', (data) => {
      console.log(`Backend: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Backend Error: ${data}`);
    });

    pythonProcess.on('close', (code) => {
      console.log(`Backend process exited with code ${code}`);
    });
  }
}

app.on('ready', () => {
  startBackend();
  createWindow();
});

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});

// Window Control IPC
ipcMain.on('window-minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window-toggle-maximize', () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  }
});

ipcMain.on('window-close', () => {
  app.quit();
});
