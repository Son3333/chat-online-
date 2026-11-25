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

app.whenReady().then(async () => {
  console.log('[Capture] Connecting PythonBridge to 127.0.0.1:8888...');
  pythonBridge = new PythonBridge('127.0.0.1', 8888);
  await pythonBridge.connect();

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

  const distIndex = path.resolve(__dirname, '..', 'frontend', 'dist', 'index.html');
  await mainWindow.loadFile(distIndex);

  // Authenticate user Vũ Duy Thái Sơn
  await mainWindow.webContents.executeJavaScript(`
    localStorage.setItem('vibe_user', JSON.stringify({
      id: 2844831592,
      username: 'sondeptrai',
      full_name: 'Vũ Duy Thái Sơn',
      avatar_color: '#2481cc',
      avatar_url: null
    }));
    window.location.reload();
  `);

  await sleep(3500);

  async function snap(fileName) {
    const img = await mainWindow.webContents.capturePage();
    const filePath = path.join(screenshotsDir, fileName);
    fs.writeFileSync(filePath, img.toPNG());
    console.log('[Snapshot Saved]:', fileName, `(${img.getSize().width}x${img.getSize().height})`);
  }

  // 1. Click select Group Chat (id 12)
  console.log('[Capture] 1. Selecting Group Chat...');
  await mainWindow.webContents.executeJavaScript(`
    const items = Array.from(document.querySelectorAll('aside div.cursor-pointer'));
    const group = items.find(el => el.textContent.includes('Nhóm') || el.textContent.includes('VIP') || el.textContent.includes('test btl'));
    if (group) group.click();
  `);
  await sleep(1500);

  // 1A. Reset to Default Theme & Snapshot (BEFORE)
  console.log('[Capture] 1A. Resetting to Default Theme (Before)...');
  await pythonBridge.sendRequest('update_conversation_theme', { conversation_id: 12, user_id: 2844831592, theme: 'default' });
  await sleep(1000);
  await snap('1_before_theme_default.png');

  // 1B. Open Theme Modal & Snapshot
  console.log('[Capture] 1B. Opening Theme Modal...');
  await mainWindow.webContents.executeJavaScript(`
    const moreBtn = document.querySelector('button[title="Tùy chọn khác"]');
    if (moreBtn) moreBtn.click();
  `);
  await sleep(500);
  await mainWindow.webContents.executeJavaScript(`
    const themeBtn = Array.from(document.querySelectorAll('div button')).find(b => b.textContent.includes('Đổi giao diện'));
    if (themeBtn) themeBtn.click();
  `);
  await sleep(800);
  await snap('1_modal_select_theme.png');

  // Close modal
  await mainWindow.webContents.executeJavaScript(`
    const closeBtn = document.querySelector('div.fixed.inset-0 button');
    if (closeBtn) closeBtn.click();
  `);
  await sleep(600);

  // 1C. Apply Sunset Theme & Snapshot (AFTER)
  console.log('[Capture] 1C. Applying Sunset Theme (After)...');
  await pythonBridge.sendRequest('update_conversation_theme', { conversation_id: 12, user_id: 2844831592, theme: 'sunset' });
  await sleep(1000);
  await snap('1_after_theme_sunset.png');

  // 1D. Apply Ocean Theme & Snapshot (AFTER)
  console.log('[Capture] 1D. Applying Ocean Theme (After)...');
  await pythonBridge.sendRequest('update_conversation_theme', { conversation_id: 12, user_id: 2844831592, theme: 'ocean' });
  await sleep(1000);
  await snap('1_after_theme_ocean.png');

  // 2. Open Group Info Modal & Snapshot
  console.log('[Capture] 2. Opening Group Info Modal...');
  await mainWindow.webContents.executeJavaScript(`
    const infoBtn = document.querySelector('button[title="Xem thông tin hội thoại"]');
    if (infoBtn) infoBtn.click();
  `);
  await sleep(1500);
  await snap('2_group_info_modal_members.png');

  // Close Group Info Modal
  await mainWindow.webContents.executeJavaScript(`
    const closeBtn = document.querySelector('div.fixed.inset-0 button');
    if (closeBtn) closeBtn.click();
  `);
  await sleep(600);

  // 3. Select Direct Chat with Pham Duc Tam & Snapshot (BEFORE NICKNAME)
  console.log('[Capture] 3. Selecting Direct Chat with Pham Duc Tam...');
  // Reset direct nickname to empty first
  await pythonBridge.sendRequest('set_conversation_nickname', {
    conversation_id: 1,
    user_id: 2844831592,
    target_user_id: 7217665131,
    nickname: ''
  });
  await sleep(500);
  await mainWindow.webContents.executeJavaScript(`
    const items = Array.from(document.querySelectorAll('aside div.cursor-pointer'));
    const directUser = items.find(el => el.textContent.includes('Pham Duc Tam') || el.textContent.includes('Tâm'));
    if (directUser) directUser.click();
  `);
  await sleep(1500);
  await snap('3_before_direct_nickname.png');

  // 3B. Open Nickname Modal & Snapshot
  console.log('[Capture] 3B. Opening Direct Nickname Modal...');
  await mainWindow.webContents.executeJavaScript(`
    const moreBtn = document.querySelector('button[title="Tùy chọn khác"]');
    if (moreBtn) moreBtn.click();
  `);
  await sleep(500);
  await mainWindow.webContents.executeJavaScript(`
    const nickBtn = Array.from(document.querySelectorAll('div button')).find(b => b.textContent.includes('Đặt biệt danh'));
    if (nickBtn) nickBtn.click();
  `);
  await sleep(800);
  await snap('3_modal_set_nickname.png');

  // 3C. Apply Nickname "Tâm Bạn Thân (KTPM)" & Snapshot (AFTER NICKNAME)
  console.log('[Capture] 3C. Setting Nickname Tâm Bạn Thân (KTPM)...');
  await pythonBridge.sendRequest('set_conversation_nickname', {
    conversation_id: 1,
    user_id: 2844831592,
    target_user_id: 7217665131,
    nickname: 'Tâm Bạn Thân (KTPM)'
  });
  await sleep(1200);
  // Close nickname prompt if still open
  await mainWindow.webContents.executeJavaScript(`
    const cancelBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent === 'Hủy');
    if (cancelBtn) cancelBtn.click();
  `);
  await sleep(800);
  await snap('3_after_direct_nickname.png');

  console.log('[Capture] ALL 8 BEFORE & AFTER SCREENSHOTS SAVED SUCCESSFULLY!');
  app.quit();
  process.exit(0);
});
