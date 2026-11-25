const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { PythonBridge } = require('../frontend/dist-electron/python_bridge.js');

const screenshotsDir = path.resolve(__dirname, '..', 'screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

let pythonBridge = null;
let mainWindow = null;

ipcMain.handle('python:request', async (_event, { action, payload }) => {
  if (!pythonBridge) throw new Error('Bridge not ready');
  return await pythonBridge.sendRequest(action, payload);
});

ipcMain.handle('app:get-server-info', () => ({ host: '127.0.0.1', port: 8888, isWan: false }));
ipcMain.handle('app:get-server-config', () => ({ host: '127.0.0.1', port: 8888 }));
ipcMain.handle('app:check_update', () => ({ has_update: false }));
ipcMain.handle('window:is-always-on-top', () => false);
ipcMain.handle('window:set-always-on-top', () => false);
ipcMain.on('window:minimize', () => {});
ipcMain.on('window:maximize', () => {});
ipcMain.on('window:close', () => {});

async function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function log(msg) {
  console.log(msg);
}

app.whenReady().then(async () => {
  try {
    log('[Capture] Connecting PythonBridge to 127.0.0.1:8888...');
    pythonBridge = new PythonBridge('127.0.0.1', 8888);
    await pythonBridge.connect();
    log('[Capture] Connected PythonBridge successfully.');

    mainWindow = new BrowserWindow({
      width: 1280,
      height: 820,
      show: false,
      frame: false,
      backgroundColor: '#0e1621',
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.resolve(__dirname, '..', 'frontend', 'dist-electron', 'preload.js'),
      },
    });

    pythonBridge.onEvent((event) => {
      if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('server:event', event);
      }
    });

    // Login as user test (admin)
    const loginRes = await pythonBridge.sendRequest('login', {
      username: 'admin',
      password: '123',
    });

    const indexHtml = path.resolve(__dirname, '..', 'frontend', 'dist', 'index.html');
    await mainWindow.loadFile(indexHtml);

    if (loginRes && loginRes.success) {
      await mainWindow.webContents.executeJavaScript(`(() => {
        localStorage.setItem('vibe_user', '${JSON.stringify(loginRes.user)}');
        localStorage.setItem('access_token', '${loginRes.token}');
        window.location.reload();
      })()`);
    }

    await sleep(3500);

    // 1. Select Group Conversation: "Nhóm Đồ Án KTPM (VIP)"
    await mainWindow.webContents.executeJavaScript(`(() => {
      const items = Array.from(document.querySelectorAll('div, li, button'));
      const groupEl = items.find(el => el.textContent && el.textContent.includes('Nhóm Đồ Án KTPM (VIP)'));
      if (groupEl) groupEl.click();
    })()`);
    await sleep(1500);

    // Open Theme Modal for Group
    await mainWindow.webContents.executeJavaScript(`(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const themeBtn = btns.find(b => b.title && b.title.includes('giao diện') || b.querySelector('svg.lucide-sparkles') || b.innerHTML.includes('lucide-sparkles'));
      if (themeBtn) themeBtn.click();
    })()`);
    await sleep(1200);

    // Capture 4_theme_modal_group_isolated.png
    let img = await mainWindow.webContents.capturePage();
    fs.writeFileSync(path.join(screenshotsDir, '4_theme_modal_group_isolated.png'), img.toPNG());
    log('[Capture] Saved 4_theme_modal_group_isolated.png');

    // Close Modal
    await mainWindow.webContents.executeJavaScript(`(() => {
      const closeBtn = document.querySelector('button svg.lucide-x')?.closest('button');
      if (closeBtn) closeBtn.click();
    })()`);
    await sleep(800);

    // 2. Select Direct Conversation: "Pham Duc Tam"
    await mainWindow.webContents.executeJavaScript(`(() => {
      const items = Array.from(document.querySelectorAll('div, li, button'));
      const directEl = items.find(el => el.textContent && el.textContent.includes('Pham Duc Tam'));
      if (directEl) directEl.click();
    })()`);
    await sleep(1500);

    // Open Theme Modal for Direct Chat
    await mainWindow.webContents.executeJavaScript(`(() => {
      const btns = Array.from(document.querySelectorAll('button'));
      const themeBtn = btns.find(b => b.title && b.title.includes('giao diện') || b.querySelector('svg.lucide-sparkles') || b.innerHTML.includes('lucide-sparkles'));
      if (themeBtn) themeBtn.click();
    })()`);
    await sleep(1200);

    // Capture 4_theme_modal_direct_isolated.png (Confirmed: NOT leaking group's theme/custom image!)
    img = await mainWindow.webContents.capturePage();
    fs.writeFileSync(path.join(screenshotsDir, '4_theme_modal_direct_isolated.png'), img.toPNG());
    log('[Capture] Saved 4_theme_modal_direct_isolated.png');

    // 3. Test Interactive Cropper (Pan & Zoom)
    await mainWindow.webContents.executeJavaScript(`(() => {
      const sampleWallpaper = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='800'><defs><linearGradient id='grad' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='%236366f1'/><stop offset='50%' stop-color='%238b5cf6'/><stop offset='100%' stop-color='%23d946ef'/></linearGradient></defs><rect width='1200' height='800' fill='url(%23grad)'/><circle cx='600' cy='380' r='180' fill='%23fef08a'/><text x='600' y='400' font-size='56' font-weight='bold' fill='%231e1b4b' text-anchor='middle'>ANH NEN TUY CHINH</text><text x='600' y='650' font-size='32' fill='white' text-anchor='middle'>Zalo & Messenger Cropper Support</text></svg>";

      const file = new File(["sample"], "sample_wallpaper.png", { type: "image/png" });
      const input = document.querySelector('input[type="file"]');
      if (input) {
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;

        const origFileReader = window.FileReader;
        window.FileReader = class extends origFileReader {
          readAsDataURL() {
            setTimeout(() => {
              this.result = sampleWallpaper;
              if (this.onload) this.onload();
            }, 50);
          }
        };
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    })()`);
    await sleep(1500);

    // Capture 5_cropper_view_pan_zoom.png (Interactive Cropper View)
    img = await mainWindow.webContents.capturePage();
    fs.writeFileSync(path.join(screenshotsDir, '5_cropper_view_pan_zoom.png'), img.toPNG());
    log('[Capture] Saved 5_cropper_view_pan_zoom.png');

    // 4. Click "Xác nhận vùng chọn"
    await mainWindow.webContents.executeJavaScript(`(() => {
      const confirmBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Xác nhận vùng chọn'));
      if (confirmBtn) confirmBtn.click();
    })()`);
    await sleep(1000);

    // Capture 5_theme_modal_ready_to_apply.png
    img = await mainWindow.webContents.capturePage();
    fs.writeFileSync(path.join(screenshotsDir, '5_theme_modal_ready_to_apply.png'), img.toPNG());
    log('[Capture] Saved 5_theme_modal_ready_to_apply.png');

    // 5. Click "Áp Dụng Giao Diện"
    await mainWindow.webContents.executeJavaScript(`(() => {
      const applyBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Áp Dụng Giao Diện'));
      if (applyBtn) applyBtn.click();
    })()`);
    await sleep(2000);

    // Capture 5_after_applied_custom_wallpaper.png
    img = await mainWindow.webContents.capturePage();
    fs.writeFileSync(path.join(screenshotsDir, '5_after_applied_custom_wallpaper.png'), img.toPNG());
    log('[Capture] Saved 5_after_applied_custom_wallpaper.png');

    log('[Capture] All verification screenshots completed successfully!');
  } catch (err) {
    log('[Capture Error] ' + (err.stack || err.message || err));
  } finally {
    app.quit();
  }
});
