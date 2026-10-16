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
exports.GitUpdater = void 0;
exports.registerUpdaterIpc = registerUpdaterIpc;
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
const electron_1 = require("electron");
class GitUpdater {
    rootDir;
    timer = null;
    isChecking = false;
    currentUpdate = null;
    mainWindow = null;
    nodeEnvPath;
    constructor(rootDir) {
        this.rootDir = rootDir;
        // Add local node tool directory to path if present
        const nodeDir = 'C:\\Users\\admin\\tools\\node-v20.18.0-win-x64';
        this.nodeEnvPath = fs.existsSync(nodeDir)
            ? `${nodeDir};${process.env.PATH || ''}`
            : (process.env.PATH || '');
    }
    setWindow(win) {
        this.mainWindow = win;
        // If an update was already detected, notify newly attached window
        if (this.currentUpdate && !win.isDestroyed()) {
            win.webContents.send('app:update_available', this.currentUpdate);
        }
    }
    startListening(intervalMs = 2000) {
        if (this.timer) {
            clearInterval(this.timer);
        }
        // Check after 2 seconds initially, then every 2000ms
        setTimeout(() => this.check(), 2000);
        this.timer = setInterval(() => this.check(), intervalMs);
    }
    stopListening() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    async check() {
        if (this.isChecking)
            return this.currentUpdate;
        if (!fs.existsSync(path.join(this.rootDir, '.git')))
            return null;
        this.isChecking = true;
        try {
            // 1. Get current local commit hash
            const localHash = await this.execCommand('git rev-parse HEAD');
            // 2. Fetch remote silently
            await this.execCommand('git fetch origin main --quiet');
            // 3. Get remote commit hash
            const remoteHash = await this.execCommand('git rev-parse origin/main');
            if (localHash && remoteHash && localHash.trim() !== remoteHash.trim()) {
                const trimmedRemote = remoteHash.trim();
                const message = await this.execCommand('git log -1 --pretty=%s origin/main');
                this.currentUpdate = {
                    remoteHash: trimmedRemote,
                    localHash: localHash.trim(),
                    message: message.trim() || 'Bản cập nhật mới từ kho mã nguồn',
                };
                if (this.mainWindow && !this.mainWindow.isDestroyed()) {
                    this.mainWindow.webContents.send('app:update_available', this.currentUpdate);
                }
                return this.currentUpdate;
            }
            else {
                this.currentUpdate = null;
            }
        }
        catch {
            // Transient network or git lock errors are silently ignored
        }
        finally {
            this.isChecking = false;
        }
        return null;
    }
    async applyUpdate() {
        try {
            console.log('[Updater] Pulling latest code and applying update...');
            // 1. Reset to latest remote
            await this.execCommand('git reset --hard origin/main');
            // 2. Build frontend
            const frontendDir = path.join(this.rootDir, 'frontend');
            if (fs.existsSync(frontendDir)) {
                await this.execCommand('npm run build', frontendDir);
                await this.execCommand('npm run build:electron', frontendDir);
            }
            // 3. Relaunch app cleanly
            console.log('[Updater] Update applied! Relaunching application...');
            electron_1.app.relaunch();
            electron_1.app.exit(0);
            return { success: true };
        }
        catch (err) {
            console.error('[Updater] Failed to apply update:', err);
            return { success: false, error: err.message || String(err) };
        }
    }
    execCommand(cmd, cwd = this.rootDir) {
        return new Promise((resolve, reject) => {
            (0, child_process_1.exec)(cmd, { cwd, env: { ...process.env, PATH: this.nodeEnvPath } }, (error, stdout) => {
                if (error) {
                    reject(error);
                }
                else {
                    resolve(stdout.trim());
                }
            });
        });
    }
}
exports.GitUpdater = GitUpdater;
function registerUpdaterIpc(updater) {
    electron_1.ipcMain.handle('app:check_update', async () => {
        return await updater.check();
    });
    electron_1.ipcMain.handle('app:apply_update', async () => {
        return await updater.applyUpdate();
    });
}
