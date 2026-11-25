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
ipcMain.handle('app:get-server-config', () => ({ host: 'bore.pub', port: 38888 }));
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
  console.log('[TestRunner] Connecting to Python server on 127.0.0.1:8888...');
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

  // Set logged in user: Vũ Duy Thái Sơn
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
    console.log('[Snapshot Saved]:', fileName);
  }

  async function clickSelector(selector) {
    return await mainWindow.webContents.executeJavaScript(`
      (() => {
        const el = document.querySelector(${JSON.stringify(selector)});
        if (el) { el.click(); return true; }
        return false;
      })()
    `);
  }

  async function clickByText(tag, text) {
    return await mainWindow.webContents.executeJavaScript(`
      (() => {
        const els = Array.from(document.querySelectorAll(${JSON.stringify(tag)}));
        const target = els.find(e => e.textContent && e.textContent.includes(${JSON.stringify(text)}));
        if (target) { target.click(); return true; }
        return false;
      })()
    `);
  }

  async function waitForModalClose() {
    for (let i = 0; i < 25; i++) {
      const hasModal = await mainWindow.webContents.executeJavaScript(`
        Boolean(document.querySelector('.fixed.inset-0'))
      `);
      if (!hasModal) return;
      await sleep(200);
    }
  }

  // --- 1. CHỌN NHÓM TRÒ CHUYỆN ---
  console.log('[TestRunner] 1. Selecting Group Chat...');
  await mainWindow.webContents.executeJavaScript(`
    const items = Array.from(document.querySelectorAll('aside div.cursor-pointer'));
    const group = items.find(el => el.textContent.includes('Nhóm') || el.textContent.includes('VIP') || el.textContent.includes('test btl'));
    if (group) group.click();
  `);
  await sleep(2000);

  // 1A. Reset về theme Mặc định
  console.log('[TestRunner] 1A. Resetting to Default theme...');
  await clickSelector('button[title="Tùy chọn khác"]');
  await sleep(500);
  await clickByText('button', 'Đổi giao diện');
  await sleep(700);
  // Snapshot Modal chọn giao diện
  await snap('1_modal_select_theme.png');
  await clickByText('div', 'Mặc định');
  await sleep(300);
  await clickByText('button', 'Áp Dụng Giao Diện');
  await waitForModalClose();
  await sleep(800);
  await snap('1_before_theme_default.png');

  // 1B. Đổi sang theme Sunset (Hoàng hôn tím)
  console.log('[TestRunner] 1B. Applying Sunset theme...');
  await clickSelector('button[title="Tùy chọn khác"]');
  await sleep(500);
  await clickByText('button', 'Đổi giao diện');
  await sleep(700);
  await clickByText('div', 'Hoàng hôn tím');
  await sleep(300);
  await clickByText('button', 'Áp Dụng Giao Diện');
  await waitForModalClose();
  await sleep(800);
  await snap('1_after_theme_sunset.png');

  // 1C. Đổi sang theme Ocean (Đại dương xanh)
  console.log('[TestRunner] 1C. Applying Ocean theme...');
  await clickSelector('button[title="Tùy chọn khác"]');
  await sleep(500);
  await clickByText('button', 'Đổi giao diện');
  await sleep(700);
  await clickByText('div', 'Đại dương xanh');
  await sleep(300);
  await clickByText('button', 'Áp Dụng Giao Diện');
  await waitForModalClose();
  await sleep(800);
  await snap('1_after_theme_ocean.png');

  // --- 2. THÔNG TIN NHÓM (MODAL THÔNG TIN NHÓM & THÀNH VIÊN) ---
  console.log('[TestRunner] 2. Opening Group Info Modal...');
  await clickSelector('button[title="Xem thông tin hội thoại"]');
  await sleep(1500);
  await snap('2_group_info_modal_members.png');

  // Đóng modal thông tin nhóm
  await mainWindow.webContents.executeJavaScript(`
    const closeBtn = Array.from(document.querySelectorAll('button')).find(b => b.querySelector('svg.lucide-x'));
    if (closeBtn) closeBtn.click();
  `);
  await waitForModalClose();
  await sleep(800);

  // --- 3. ĐẶT BIỆT DANH BẠN CHAT (DIRECT CHAT) ---
  console.log('[TestRunner] 3. Selecting Direct Chat with Pham Duc Tam...');
  await mainWindow.webContents.executeJavaScript(`
    const items = Array.from(document.querySelectorAll('aside div.cursor-pointer'));
    const directUser = items.find(el => el.textContent.includes('Pham Duc Tam'));
    if (directUser) directUser.click();
  `);
  await sleep(1800);
  await snap('3_before_direct_nickname.png');

  // Mở popup "Đặt biệt danh cho bạn chat"
  console.log('[TestRunner] 3B. Opening Nickname Modal...');
  await clickSelector('button[title="Tùy chọn khác"]');
  await sleep(500);
  await clickByText('button', 'Đặt biệt danh');
  await sleep(700);
  await snap('3_modal_set_nickname.png');

  // Nhập biệt danh mới "Tâm Bạn Thân (KTPM)" và Lưu
  console.log('[TestRunner] 3C. Saving Nickname...');
  await mainWindow.webContents.executeJavaScript(`
    const input = document.querySelector('input[placeholder*="biệt danh"]');
    if (input) {
      input.value = 'Tâm Bạn Thân (KTPM)';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  `);
  await sleep(300);
  await clickByText('button', 'Lưu biệt danh');
  await sleep(1500);
  await snap('3_after_direct_nickname.png');

  console.log('[TestRunner] ALL SCREENSHOTS COMPLETED SUCCESSFULLY!');
  app.quit();
  process.exit(0);
});
