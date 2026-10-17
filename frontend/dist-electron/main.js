"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
// Self-heal: If mistakenly launched with ELECTRON_RUN_AS_NODE (e.g. from VS Code/IDE terminal or inherited env)
const _electronCheck = require('electron');
if (typeof _electronCheck === 'string' || !_electronCheck.app) {
    const electronExe = typeof _electronCheck === 'string' ? _electronCheck : process.execPath;
    const { spawn: _spawn } = require('child_process');
    const pathMod = require('path');
    const cleanEnv = { ...process.env };
    delete cleanEnv.ELECTRON_RUN_AS_NODE;
    const child = _spawn(electronExe, ['.'], {
        cwd: pathMod.resolve(__dirname, '..'),
        detached: true,
        stdio: 'ignore',
        env: cleanEnv,
    });
    child.unref();
    process.exit(0);
}
const electron_1 = require("electron");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const net = __importStar(require("net"));
const child_process_1 = require("child_process");
const python_bridge_1 = require("./python_bridge");
const updater_1 = require("./updater");
// Ghi log lỗi vào file nếu có sự cố crash bất ngờ
process.on('uncaughtException', (err) => {
    try {
        const rootDir = path.resolve(__dirname, '../../');
        fs.appendFileSync(path.join(rootDir, 'crash_log.txt'), `[Crash ${new Date().toISOString()}] ${err.stack || err}\n`);
    }
    catch { }
    console.error('[Uncaught Exception]', err);
});
let mainWindow = null;
let pythonProcess = null;
let pythonBridge = null;
let gitUpdater = null;
const isDev = process.env.NODE_ENV === 'development' || (typeof electron_1.app !== 'undefined' && electron_1.app ? !electron_1.app.isPackaged : false);
let PORT = 8888;
let HOST = '127.0.0.1';
// Kiểm tra xem port 8888 đã có server chạy chưa
function checkPortAvailable(port, host) {
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
async function resolveServerEndpoint() {
    const rootDir = path.resolve(__dirname, '../../');
    const serverScript = path.join(rootDir, 'src', 'server', 'server.py');
    // 1. Nếu đây là máy tính có mã nguồn server (Máy Chủ Host) -> LUÔN LUÔN kết nối trực tiếp 127.0.0.1:8888
    if (fs.existsSync(serverScript)) {
        console.log('[Main] Host machine detected. Connecting locally via 127.0.0.1:8888 (0ms ping)');
        return { host: '127.0.0.1', port: 8888, isWan: false };
    }
    // 2. Kiểm tra nếu có Server cục bộ đang chạy trên chính máy tính này
    const isLocalRunning = await checkPortAvailable(8888, '127.0.0.1');
    if (isLocalRunning) {
        console.log('[Main] Local Python server detected on 127.0.0.1:8888 (Host mode, 0ms ping)');
        return { host: '127.0.0.1', port: 8888, isWan: false };
    }
    // 3. Nếu là máy Client từ xa: Đọc cấu hình từ server_config.json nếu có
    const cfgPath = path.join(rootDir, 'server_config.json');
    if (fs.existsSync(cfgPath)) {
        try {
            const data = JSON.parse(fs.readFileSync(cfgPath, 'utf-8'));
            if (data.host && data.port) {
                const h = String(data.host).trim();
                const p = Number(data.port);
                console.log(`[Main] Remote client configured from server_config.json: ${h}:${p}`);
                return { host: h, port: p, isWan: h !== '127.0.0.1' && h !== 'localhost' };
            }
        }
        catch { }
    }
    // 4. Mặc định dự phòng cho máy trạm
    return { host: '127.0.0.1', port: 8888, isWan: false };
}
async function startPythonBackendIfNeeded() {
    const isServerRunning = await checkPortAvailable(8888, '127.0.0.1');
    if (isServerRunning) {
        console.log('[Main] Python Chat Server is already running on port 8888');
        return;
    }
    // Khởi chạy server ngầm nếu máy này có mã nguồn backend
    const rootDir = path.resolve(__dirname, '../../');
    const wanScript = path.join(rootDir, 'run_server_wan.py');
    const localScript = path.join(rootDir, 'src', 'server', 'server.py');
    const scriptToRun = fs.existsSync(wanScript) ? wanScript : (fs.existsSync(localScript) ? localScript : null);
    if (scriptToRun) {
        console.log('[Main] Spawning independent Python server process:', scriptToRun);
        try {
            pythonProcess = (0, child_process_1.spawn)('python', ['-u', scriptToRun], {
                cwd: rootDir,
                detached: true,
                stdio: 'ignore',
            });
            pythonProcess.unref();
            // Chờ server sẵn sàng trên port 8888
            for (let i = 0; i < 20; i++) {
                await new Promise((r) => setTimeout(r, 400));
                if (await checkPortAvailable(8888, '127.0.0.1')) {
                    console.log('[Main] Python server is up and ready on 127.0.0.1:8888!');
                    break;
                }
            }
        }
        catch (err) {
            console.warn('[Main] Could not spawn python process:', err);
        }
    }
    else {
        console.log('[Main] Remote client machine detected. No local server script to spawn.');
    }
}
async function createWindow() {
    mainWindow = new electron_1.BrowserWindow({
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
    pythonBridge = new python_bridge_1.PythonBridge(HOST, PORT);
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
    }
    else if (fs.existsSync(indexPath)) {
        mainWindow.loadFile(indexPath);
    }
    else {
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
            electron_1.shell.openExternal(url);
        }
        return { action: 'deny' };
    });
    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}
// IPC Handlers
electron_1.ipcMain.handle('app:open-external', async (_event, url) => {
    if (url && (url.startsWith('https://') || url.startsWith('http://'))) {
        await electron_1.shell.openExternal(url);
        return true;
    }
    return false;
});
electron_1.ipcMain.handle('python:request', async (_event, { action, payload }) => {
    if (!pythonBridge) {
        throw new Error('Python bridge not initialized');
    }
    return await pythonBridge.sendRequest(action, payload);
});
electron_1.ipcMain.on('window:minimize', () => {
    mainWindow?.minimize();
});
electron_1.ipcMain.on('window:maximize', () => {
    if (mainWindow?.isMaximized()) {
        mainWindow.unmaximize();
    }
    else {
        mainWindow?.maximize();
    }
});
electron_1.ipcMain.on('window:close', () => {
    mainWindow?.close();
});
electron_1.ipcMain.handle('window:set-always-on-top', (_event, enabled) => {
    if (mainWindow) {
        mainWindow.setAlwaysOnTop(enabled);
        return mainWindow.isAlwaysOnTop();
    }
    return false;
});
electron_1.ipcMain.handle('window:is-always-on-top', () => {
    return mainWindow?.isAlwaysOnTop() ?? false;
});
electron_1.ipcMain.handle('dialog:select-file', async (_event, category) => {
    if (!mainWindow)
        return { canceled: true };
    let filters = [];
    if (category === 'image') {
        filters = [
            { name: 'Hình ảnh (PNG, JPG, GIF, WebP)', extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'] },
            { name: 'Mọi tệp tin', extensions: ['*'] },
        ];
    }
    else if (category === 'video') {
        filters = [
            { name: 'Video (MP4, WebM, MOV, MKV)', extensions: ['mp4', 'webm', 'mov', 'mkv', 'avi'] },
            { name: 'Mọi tệp tin', extensions: ['*'] },
        ];
    }
    else {
        filters = [
            { name: 'Mọi tệp tin & Tài liệu', extensions: ['*'] },
            { name: 'Tài liệu văn phòng', extensions: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt'] },
            { name: 'Tệp nén', extensions: ['zip', 'rar', '7z', 'tar', 'gz'] },
        ];
    }
    const result = await electron_1.dialog.showOpenDialog(mainWindow, {
        properties: ['openFile'],
        filters,
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
        category,
    };
});
electron_1.ipcMain.handle('dialog:save-file', async (_event, { fileName, base64Data }) => {
    if (!mainWindow)
        return { success: false };
    const result = await electron_1.dialog.showSaveDialog(mainWindow, {
        defaultPath: fileName,
    });
    if (result.canceled || !result.filePath) {
        return { success: false };
    }
    try {
        const buffer = Buffer.from(base64Data, 'base64');
        fs.writeFileSync(result.filePath, buffer);
        return { success: true, path: result.filePath };
    }
    catch (err) {
        return { success: false, error: err.message };
    }
});
electron_1.ipcMain.handle('app:get-server-info', () => {
    const rootDir = path.resolve(__dirname, '../../');
    const wanInfoPath = path.join(rootDir, 'wan_server_info.txt');
    if (fs.existsSync(wanInfoPath)) {
        try {
            const content = fs.readFileSync(wanInfoPath, 'utf-8');
            const match = content.match(/FULL=(.+)/);
            if (match && match[1]) {
                return { isWan: true, address: match[1].trim(), host: HOST, port: PORT };
            }
        }
        catch {
            // fallback
        }
    }
    const isWan = HOST !== '127.0.0.1' && HOST !== 'localhost';
    return { isWan, address: `${HOST}:${PORT}`, host: HOST, port: PORT };
});
electron_1.ipcMain.handle('app:get-server-config', () => {
    return {
        host: HOST,
        port: PORT,
        isWan: HOST !== '127.0.0.1' && HOST !== 'localhost',
    };
});
electron_1.ipcMain.handle('app:set-server-config', async (_event, { host, port }) => {
    HOST = host.trim();
    PORT = Number(port);
    const rootDir = path.resolve(__dirname, '../../');
    const cfgPath = path.join(rootDir, 'server_config.json');
    try {
        fs.writeFileSync(cfgPath, JSON.stringify({ host: HOST, port: PORT }, null, 2), 'utf-8');
    }
    catch (e) {
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
electron_1.ipcMain.handle('media:get-screen-source-id', async () => {
    try {
        const sources = await electron_1.desktopCapturer.getSources({ types: ['screen', 'window'] });
        if (sources.length > 0) {
            return sources[0].id;
        }
    }
    catch (err) {
        console.error('[Main] desktopCapturer getSources error:', err);
    }
    return null;
});
electron_1.app.whenReady().then(async () => {
    // Grant all media permissions (Microphone, Camera, Screen Share, Geolocation)
    electron_1.session.defaultSession.setPermissionRequestHandler((_webContents, permission, callback) => {
        callback(true);
    });
    // Setup display media request handler for getDisplayMedia screen sharing
    electron_1.session.defaultSession.setDisplayMediaRequestHandler((_request, callback) => {
        electron_1.desktopCapturer
            .getSources({ types: ['screen', 'window'] })
            .then((sources) => {
            if (sources.length > 0) {
                callback({ video: sources[0] });
            }
            else {
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
    gitUpdater = new updater_1.GitUpdater(rootDir);
    (0, updater_1.registerUpdaterIpc)(gitUpdater);
    gitUpdater.startListening(2000);
    await createWindow();
    electron_1.app.on('activate', () => {
        if (electron_1.BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});
electron_1.app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        electron_1.app.quit();
    }
});
electron_1.app.on('before-quit', () => {
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
