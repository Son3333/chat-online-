import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import * as net from 'net';
import { spawn, ChildProcess } from 'child_process';
import { PythonBridge } from './python_bridge';
import { GitUpdater, registerUpdaterIpc } from './updater';

let mainWindow: BrowserWindow | null = null;
let pythonProcess: ChildProcess | null = null;
let pythonBridge: PythonBridge | null = null;
let gitUpdater: GitUpdater | null = null;

const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;
const PORT = 8888;
const HOST = '127.0.0.1';

// Kiểm tra xem port 8888 đã có server chạy chưa
function checkPortAvailable(port: number, host: string): Promise<boolean> {
  return new Promise((resolve) => {
    const s = new net.Socket();
    s.setTimeout(1000);
    s.on('connect', () => {
      s.destroy();
      resolve(true); // Có server đang chạy
    });
    s.on('error', () => {
      s.destroy();
      resolve(false); // Không có server
    });
    s.on('timeout', () => {
      s.destroy();
      resolve(false);
    });
    s.connect(port, host);
  });
}

async function startPythonBackendIfNeeded(): Promise<void> {
  const isServerRunning = await checkPortAvailable(PORT, HOST);
  if (isServerRunning) {
    console.log('[Main] Python Chat Server is already running on port', PORT);
    return;
  }

  // Khởi chạy server.py
  const rootDir = path.resolve(__dirname, '../../');
  const serverScript = path.join(rootDir, 'src', 'server', 'server.py');
  if (fs.existsSync(serverScript)) {
    console.log('[Main] Spawning Python server:', serverScript);
    pythonProcess = spawn('python', [serverScript], {
      cwd: rootDir,
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    pythonProcess.stdout?.on('data', (d) => console.log('[Python Server]', d.toString().trim()));
    pythonProcess.stderr?.on('data', (d) => console.error('[Python Server Error]', d.toString().trim()));

    pythonProcess.on('exit', (code) => {
      console.log('[Main] Python server exited with code', code);
      pythonProcess = null;
    });

    // Chờ server sẵn sàng
    for (let i = 0; i < 15; i++) {
      await new Promise((r) => setTimeout(r, 400));
      if (await checkPortAvailable(PORT, HOST)) {
        console.log('[Main] Python server is up and ready!');
        break;
      }
    }
  } else {
    console.warn('[Main] Server script not found at', serverScript);
  }
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 820,
    minWidth: 920,
    minHeight: 640,
    frame: false, // Custom Telegram-style titlebar
    titleBarStyle: 'hidden',
    backgroundColor: '#0e1621',
    icon: fs.existsSync(path.join(__dirname, '../../app.ico'))
      ? path.join(__dirname, '../../app.ico')
      : path.join(__dirname, '../public/logo.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });

  // Setup Python Bridge
  pythonBridge = new PythonBridge(HOST, PORT);
  await pythonBridge.connect();

  // Forward push events from Python to React renderer
  pythonBridge.onEvent((event) => {
    if (mainWindow && !mainWindow.isDestroyed()) {
      mainWindow.webContents.send('server:event', event);
    }
  });

  // Load built React UI directly
  const indexPath = path.join(__dirname, '../dist/index.html');
  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL);
  } else if (fs.existsSync(indexPath)) {
    mainWindow.loadFile(indexPath);
  } else {
    mainWindow.loadURL('http://localhost:5173').catch((err) => {
      console.error('[Main] Failed to load UI:', err);
    });
  }

  if (gitUpdater) {
    gitUpdater.setWindow(mainWindow);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('python:request', async (_event, { action, payload }) => {
  if (!pythonBridge) {
    throw new Error('Python bridge not initialized');
  }
  return await pythonBridge.sendRequest(action, payload);
});

ipcMain.on('window:minimize', () => {
  mainWindow?.minimize();
});

ipcMain.on('window:maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});

ipcMain.on('window:close', () => {
  mainWindow?.close();
});

ipcMain.handle('window:set-always-on-top', (_event, enabled: boolean) => {
  if (mainWindow) {
    mainWindow.setAlwaysOnTop(enabled);
    return mainWindow.isAlwaysOnTop();
  }
  return false;
});

ipcMain.handle('window:is-always-on-top', () => {
  return mainWindow?.isAlwaysOnTop() ?? false;
});

ipcMain.handle('dialog:select-file', async () => {
  if (!mainWindow) return { canceled: true };
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [
      { name: 'Mọi tệp tin & Hình ảnh', extensions: ['*'] },
      { name: 'Hình ảnh', extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'] },
      { name: 'Tài liệu', extensions: ['pdf', 'docx', 'xlsx', 'txt', 'zip'] },
    ],
  });

  if (result.canceled || result.filePaths.length === 0) {
    return { canceled: true };
  }

  const filePath = result.filePaths[0];
  const stat = fs.statSync(filePath);
  const data = fs.readFileSync(filePath);
  const base64Data = data.toString('base64');
  const fileName = path.basename(filePath);

  return {
    canceled: false,
    fileName,
    fileSize: stat.size,
    fileData: base64Data,
  };
});

ipcMain.handle('dialog:save-file', async (_event, { fileName, base64Data }) => {
  if (!mainWindow) return { success: false };
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: fileName,
  });

  if (result.canceled || !result.filePath) {
    return { success: false };
  }

  try {
    const buffer = Buffer.from(base64Data, 'base64');
    fs.writeFileSync(result.filePath, buffer);
    return { success: true, path: result.filePath };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
});

app.whenReady().then(async () => {
  await startPythonBackendIfNeeded();

  // Setup 2-second Git update listener
  const rootDir = path.resolve(__dirname, '../../');
  gitUpdater = new GitUpdater(rootDir);
  registerUpdaterIpc(gitUpdater);
  gitUpdater.startListening(2000);

  await createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (gitUpdater) {
    gitUpdater.stopListening();
  }
  if (pythonBridge) {
    pythonBridge.disconnect();
  }
  if (pythonProcess) {
    console.log('[Main] Killing spawned Python server process...');
    pythonProcess.kill();
    pythonProcess = null;
  }
});

