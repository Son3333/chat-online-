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
const https = __importStar(require("https"));
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
    startListening(intervalMs = 120000) {
        if (this.timer) {
            clearInterval(this.timer);
        }
        // Check after 5 seconds initially, then every intervalMs
        setTimeout(() => this.check(), 5000);
        this.timer = setInterval(() => this.check(), intervalMs);
    }
    stopListening() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    async getLocalHash() {
        // 1. Try git rev-parse HEAD if .git exists
        if (fs.existsSync(path.join(this.rootDir, '.git'))) {
            try {
                const hash = await this.execCommand('git rev-parse HEAD');
                if (hash && hash.length >= 7)
                    return hash.trim();
            }
            catch { }
        }
        // 2. Fallback to version.json (especially for ZIP download without .git)
        const versionPath = path.join(this.rootDir, 'version.json');
        if (fs.existsSync(versionPath)) {
            try {
                const data = JSON.parse(fs.readFileSync(versionPath, 'utf-8'));
                if (data.commit)
                    return String(data.commit).trim();
            }
            catch { }
        }
        return null;
    }
    async fetchRemoteGithubApi() {
        return new Promise((resolve) => {
            const options = {
                hostname: 'api.github.com',
                path: '/repos/Son3333/chat-online-/commits/main',
                headers: {
                    'User-Agent': 'Vibe-Nguoi-Tot-Updater',
                    'Accept': 'application/vnd.github.v3+json',
                },
                timeout: 6000,
            };
            const req = https.get(options, (res) => {
                if (res.statusCode !== 200) {
                    resolve(null);
                    return;
                }
                let body = '';
                res.on('data', (chunk) => { body += chunk; });
                res.on('end', () => {
                    try {
                        const data = JSON.parse(body);
                        if (data && data.sha) {
                            const msg = data.commit?.message ? data.commit.message.split('\n')[0].trim() : 'Bản cập nhật mới từ kho mã nguồn';
                            resolve({ sha: data.sha.trim(), message: msg });
                        }
                        else {
                            resolve(null);
                        }
                    }
                    catch {
                        resolve(null);
                    }
                });
            });
            req.on('error', () => resolve(null));
            req.on('timeout', () => {
                req.destroy();
                resolve(null);
            });
        });
    }
    async check() {
        if (this.isChecking)
            return this.currentUpdate;
        this.isChecking = true;
        try {
            const localHash = await this.getLocalHash();
            if (!localHash)
                return null;
            let remoteHash = null;
            let message = 'Bản cập nhật mới từ kho mã nguồn';
            // 1. Try Git CLI first if .git exists
            if (fs.existsSync(path.join(this.rootDir, '.git'))) {
                try {
                    await this.execCommand('git fetch origin main --quiet');
                    const rHash = await this.execCommand('git rev-parse origin/main');
                    if (rHash) {
                        remoteHash = rHash.trim();
                        const msg = await this.execCommand('git log -1 --pretty=%s origin/main');
                        if (msg)
                            message = msg.trim();
                    }
                }
                catch {
                    // Fall back to GitHub REST API
                }
            }
            // 2. If Git CLI didn't get remoteHash, fetch from GitHub REST API directly
            if (!remoteHash) {
                const apiResult = await this.fetchRemoteGithubApi();
                if (apiResult) {
                    remoteHash = apiResult.sha;
                    message = apiResult.message;
                }
            }
            if (remoteHash) {
                const localPrefix = localHash.slice(0, 7).toLowerCase();
                const remotePrefix = remoteHash.slice(0, 7).toLowerCase();
                if (localPrefix !== remotePrefix) {
                    this.currentUpdate = {
                        remoteHash: remoteHash.trim(),
                        localHash: localHash.trim(),
                        message,
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
        }
        catch {
            // Ignore transient network errors
        }
        finally {
            this.isChecking = false;
        }
        return null;
    }
    async applyUpdate() {
        try {
            console.log('[Updater] Pulling latest code and applying update...');
            // 1. Reset to latest remote if git is available
            if (fs.existsSync(path.join(this.rootDir, '.git'))) {
                try {
                    await this.execCommand('git reset --hard origin/main');
                }
                catch {
                    await this.execCommand('git pull origin main');
                }
            }
            // 2. Build frontend (chỉ thực hiện nếu máy trạm có cài node_modules để phát triển)
            const frontendDir = path.join(this.rootDir, 'frontend');
            const nodeModulesDir = path.join(frontendDir, 'node_modules');
            if (fs.existsSync(nodeModulesDir)) {
                try {
                    await this.execCommand('npm run build', frontendDir);
                    await this.execCommand('npm run build:electron', frontendDir);
                }
                catch (buildErr) {
                    console.warn('[Updater] Rebuild skipped, using prebuilt dist files from Git repo:', buildErr);
                }
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
