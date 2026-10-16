import { exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { BrowserWindow, app, ipcMain } from 'electron';

export interface UpdateInfo {
  remoteHash: string;
  localHash: string;
  message: string;
}

export class GitUpdater {
  private rootDir: string;
  private timer: NodeJS.Timeout | null = null;
  private isChecking: boolean = false;
  private currentUpdate: UpdateInfo | null = null;
  private mainWindow: BrowserWindow | null = null;
  private nodeEnvPath: string;

  constructor(rootDir: string) {
    this.rootDir = rootDir;
    // Add local node tool directory to path if present
    const nodeDir = 'C:\\Users\\admin\\tools\\node-v20.18.0-win-x64';
    this.nodeEnvPath = fs.existsSync(nodeDir)
      ? `${nodeDir};${process.env.PATH || ''}`
      : (process.env.PATH || '');
  }

  public setWindow(win: BrowserWindow) {
    this.mainWindow = win;
    // If an update was already detected, notify newly attached window
    if (this.currentUpdate && !win.isDestroyed()) {
      win.webContents.send('app:update_available', this.currentUpdate);
    }
  }

  public startListening(intervalMs = 2000) {
    if (this.timer) {
      clearInterval(this.timer);
    }
    // Check after 2 seconds initially, then every 2000ms
    setTimeout(() => this.check(), 2000);
    this.timer = setInterval(() => this.check(), intervalMs);
  }

  public stopListening() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  public async check(): Promise<UpdateInfo | null> {
    if (this.isChecking) return this.currentUpdate;
    if (!fs.existsSync(path.join(this.rootDir, '.git'))) return null;

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
      } else {
        this.currentUpdate = null;
      }
    } catch {
      // Transient network or git lock errors are silently ignored
    } finally {
      this.isChecking = false;
    }
    return null;
  }

  public async applyUpdate(): Promise<{ success: boolean; error?: string }> {
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
      app.relaunch();
      app.exit(0);
      return { success: true };
    } catch (err: any) {
      console.error('[Updater] Failed to apply update:', err);
      return { success: false, error: err.message || String(err) };
    }
  }

  private execCommand(cmd: string, cwd = this.rootDir): Promise<string> {
    return new Promise((resolve, reject) => {
      exec(cmd, { cwd, env: { ...process.env, PATH: this.nodeEnvPath } }, (error, stdout) => {
        if (error) {
          reject(error);
        } else {
          resolve(stdout.trim());
        }
      });
    });
  }
}

export function registerUpdaterIpc(updater: GitUpdater) {
  ipcMain.handle('app:check_update', async () => {
    return await updater.check();
  });

  ipcMain.handle('app:apply_update', async () => {
    return await updater.applyUpdate();
  });
}

