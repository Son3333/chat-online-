import { app, BrowserWindow, ipcMain, dialog, session, desktopCapturer, shell } from 'electron';
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

const isDev = process.env.NODE_ENV === 'development' || (typeof app !== 'undefined' && app ? !app.isPackaged : false);
let PORT = 8888;
let HOST = '127.0.0.1';

// Kiểm tra xem port 8888 đã có server chạy chưa
function checkPortAvailable(port: number, host: string): Promise<boolean> {
  return new Promise((resolve) => {
    const s = new net.Socket();
    s.setTimeout(1200);
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

// Tự động phân giải địa chỉ máy chủ phù hợp (Cục bộ localhost hoặc Mạng Internet WAN)
async function resolveServerEndpoint(): Promise<{ host: string; port: number; isWan: boolean }> {
  const rootDir = path.resolve(__dirname, '../../');
  const cfgPath = path.join(rootDir, 'server_config.json');

  // 1. Kiểm tra cấu hình thủ công trong server_config.json nếu có
  if (fs.existsSync(cfgPath)) {
    try {
      const data = JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
      if (data.host && data.port) {
        const h = String(data.host).trim();
        const p = Number(data.port);
        console.log(`[Main] Using configured server from server_config.json: ${h}:${p}`);
        return { host: h, port: p, isWan: h !== '127.0.0.1' && h !== 'localhost' };
      }
    } catch {}
  }

  // 2. Kiểm tra nếu có Server cục bộ đang chạy trên chính máy tính này (Máy Chủ Host)
  const isLocalRunning = await checkPortAvailable(8888, '127.0.0.1');
  if (isLocalRunning) {
    console.log('[Main] Local Python server detected on 127.0.0.1:8888');
    return { host: '127.0.0.1', port: 8888, isWan: false };
  }

  // 3. Nếu máy này không chạy server cục bộ -> Đây là Máy Khác (Client từ xa)
  // Kết nối trực tiếp tới Server WAN mặc định trên Internet: bore.pub:38888!
  console.log('[Main] No local server running. Auto-connecting to online WAN Server: bore.pub:38888');
  return { host: 'bore.pub', port: 38888, isWan: true };
}

async function startPythonBackendIfNeeded(): Promise<void> {
  // Chỉ khởi chạy server ngầm nếu kết nối vào chính máy này (127.0.0.1)
  if (HOST !== '127.0.0.1' && HOST !== 'localhost') {
    console.log(`[Main] Client configured to remote server (${HOST}:${PORT}). Skipping local server spawn.`);
    return;
  }

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

  // Open external links (such as Google Maps) in default system browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// IPC Handlers
ipcMain.handle('app:open-external', async (_event, url: string) => {
  if (url && (url.startsWith('https://') || url.startsWith('http://'))) {
    await shell.openExternal(url);
    return true;
  }
  return false;
});

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
      { name: 'Mọi tệp tin & Đa phương tiện', extensions: ['*'] },
      { name: 'Hình ảnh', extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'] },
      { name: 'Video & Clip', extensions: ['mp4', 'webm', 'mov', 'mkv', 'avi'] },
      { name: 'Tài liệu', extensions: ['pdf', 'docx', 'xlsx', 'txt', 'zip', 'rar'] },
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

ipcMain.handle('app:get-server-info', () => {
  const rootDir = path.resolve(__dirname, '../../');
  const wanInfoPath = path.join(rootDir, 'wan_server_info.txt');
  if (fs.existsSync(wanInfoPath)) {
    try {
      const content = fs.readFileSync(wanInfoPath, 'utf-8');
      const match = content.match(/FULL=(.+)/);
      if (match && match[1]) {
        return { isWan: true, address: match[1].trim(), host: HOST, port: PORT };
      }
    } catch {
      // fallback
    }
  }
  const isWan = HOST !== '127.0.0.1' && HOST !== 'localhost';
  return { isWan, address: `${HOST}:${PORT}`, host: HOST, port: PORT };
});

ipcMain.handle('app:get-server-config', () => {
  return {
    host: HOST,
    port: PORT,
    isWan: HOST !== '127.0.0.1' && HOST !== 'localhost',
  };
});

ipcMain.handle('app:set-server-config', async (_event, { host, port }: { host: string; port: number }) => {
  HOST = host.trim();
  PORT = Number(port);
  const rootDir = path.resolve(__dirname, '../../');
  const cfgPath = path.join(rootDir, 'server_config.json');
  try {
    fs.writeFileSync(cfgPath, JSON.stringify({ host: HOST, port: PORT }, null, 2), 'utf-8');
  } catch (e) {
    console.warn('[Main] Could not write server_config.json:', e);
  }

  if (pythonBridge) {
    pythonBridge.setEndpoint(HOST, PORT);
    const ok = await pythonBridge.connect();
    return {
      host: HOST,
      port: PORT,
      isWan: HOST !== '127.0.0.1' && HOST !== 'localhost',
      connected: ok,
    };
  }
  return {
    host: HOST,
    port: PORT,
    isWan: HOST !== '127.0.0.1' && HOST !== 'localhost',
    connected: false,
  };
});

// Media permissions and Screen Sharing Handlers
ipcMain.handle('media:get-screen-source-id', async () => {
  try {
    const sources = await desktopCapturer.getSources({ types: ['screen', 'window'] });
    if (sources.length > 0) {
      return sources[0].id;
    }
  } catch (err) {
    console.error('[Main] desktopCapturer getSources error:', err);
  }
  return null;
});

app.whenReady().then(async () => {
  // Grant all media permissions (Microphone, Camera, Screen Share, Geolocation)
  session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
    callback(true);
  });

  // Setup display media request handler for getDisplayMedia screen sharing
  session.defaultSession.setDisplayMediaRequestHandler((_request, callback) => {
    desktopCapturer
      .getSources({ types: ['screen', 'window'] })
      .then((sources) => {
        if (sources.length > 0) {
          callback({ video: sources[0] });
        } else {
          callback({});
        }
      })
      .catch((err) => {
        console.error('[Main] setDisplayMediaRequestHandler error:', err);
        callback({});
      });
  });

  // Tự động phân giải server endpoint (máy chủ localhost hay WAN remote)
  const endpoint = await resolveServerEndpoint();
  HOST = endpoint.host;
  PORT = endpoint.port;

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

