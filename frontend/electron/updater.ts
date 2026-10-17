import { exec } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as https from 'https';
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

  public startListening(intervalMs = 120000) {
    if (this.timer) {
      clearInterval(this.timer);
    }
    // Check after 5 seconds initially, then every intervalMs
    setTimeout(() => this.check(), 5000);
    this.timer = setInterval(() => this.check(), intervalMs);
  }

  public stopListening() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private async getLocalHash(): Promise<string | null> {
    // 1. Try git rev-parse HEAD if .git exists
    if (fs.existsSync(path.join(this.rootDir, '.git'))) {
      try {
        const hash = await this.execCommand('git rev-parse HEAD');
        if (hash && hash.length >= 7) return hash.trim();
      } catch {}
    }

    // 2. Fallback to version.json (especially for ZIP download without .git)
    const versionPath = path.join(this.rootDir, 'version.json');
    if (fs.existsSync(versionPath)) {
      try {
        const data = JSON.parse(fs.readFileSync(versionPath, 'utf-8'));
        if (data.commit) return String(data.commit).trim();
      } catch {}
    }
    return null;
  }

  private async fetchRemoteGithubApi(): Promise<{ sha: string; message: string } | null> {
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
            } else {
              resolve(null);
            }
          } catch {
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

  public async check(): Promise<UpdateInfo | null> {
    if (this.isChecking) return this.currentUpdate;
    this.isChecking = true;

    try {
      const localHash = await this.getLocalHash();
      if (!localHash) return null;

      let remoteHash: string | null = null;
      let message = 'Bản cập nhật mới từ kho mã nguồn';

      // 1. Try Git CLI first if .git exists
      if (fs.existsSync(path.join(this.rootDir, '.git'))) {
        try {
          await this.execCommand('git fetch origin main --quiet');
          const rHash = await this.execCommand('git rev-parse origin/main');
          if (rHash) {
            remoteHash = rHash.trim();
            const msg = await this.execCommand('git log -1 --pretty=%s origin/main');
            if (msg) message = msg.trim();
          }
        } catch {
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
        } else {
          this.currentUpdate = null;
        }
      }
    } catch {
      // Ignore transient network errors
    } finally {
      this.isChecking = false;
    }
    return null;
  }

  public async applyUpdate(): Promise<{ success: boolean; error?: string }> {
    try {
      console.log('[Updater] Pulling latest code and applying update...');
      // 1. Reset to latest remote if git is available
      if (fs.existsSync(path.join(this.rootDir, '.git'))) {
        try {
          await this.execCommand('git reset --hard origin/main');
        } catch {
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
        } catch (buildErr) {
          console.warn('[Updater] Rebuild skipped, using prebuilt dist files from Git repo:', buildErr);
        }
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

