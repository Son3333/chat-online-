const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { PythonBridge } = require('../frontend/dist-electron/python_bridge.js');

const screenshotsDir = path.resolve(__dirname, '..', 'screenshots');

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

  await sleep(2500);

  async function snap(fileName) {
    const img = await mainWindow.webContents.capturePage();
    const filePath = path.join(screenshotsDir, fileName);
    fs.writeFileSync(filePath, img.toPNG());
    console.log('[Snapshot Saved]:', fileName);
  }

  // 1. Reset direct nickname in DB to empty
  console.log('[Capture] 1. Resetting nickname in DB...');
  await pythonBridge.sendRequest('set_conversation_nickname', {
    conversation_id: 1,
    user_id: 2844831592,
    target_user_id: 7217665131,
    nickname: ''
  });
  await sleep(500);

  // 2. Click Pham Duc Tam direct chat
  console.log('[Capture] 2. Clicking Pham Duc Tam card in sidebar...');
  await mainWindow.webContents.executeJavaScript(`
    (() => {
      const spans = Array.from(document.querySelectorAll('aside span'));
      const tamSpan = spans.find(s => s.textContent && s.textContent.trim().includes('Pham Duc Tam'));
      if (tamSpan) {
        const card = tamSpan.closest('div.cursor-pointer');
        if (card) card.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
      }
    })()
  `);
  await sleep(1500);
  await snap('3_before_direct_nickname.png');

  // 3. Open More Menu -> Đặt biệt danh cho bạn chat
  console.log('[Capture] 3. Opening Nickname prompt...');
  await mainWindow.webContents.executeJavaScript(`
    const moreBtn = document.querySelector('button[title="Tùy chọn khác"]');
    if (moreBtn) moreBtn.click();
  `);
  await sleep(500);
  await mainWindow.webContents.executeJavaScript(`
    const buttons = Array.from(document.querySelectorAll('div button'));
    const nickBtn = buttons.find(b => b.textContent && b.textContent.includes('Đặt biệt danh'));
    if (nickBtn) nickBtn.click();
  `);
  await sleep(800);
  await snap('3_modal_set_nickname.png');

  // 4. Type Nickname & Click Save
  console.log('[Capture] 4. Typing nickname Tâm Bạn Thân (KTPM) & saving...');
  await mainWindow.webContents.executeJavaScript(`
    (() => {
      const input = document.querySelector('input[placeholder*="biệt danh"]');
      if (input) {
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(input, 'Tâm Bạn Thân (KTPM)');
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
      const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('Lưu Biệt Danh'));
      if (saveBtn) saveBtn.click();
    })()
  `);
  await sleep(2000);
  await snap('3_after_direct_nickname.png');

  console.log('[Capture] ALL DIRECT NICKNAME SNAPSHOTS DONE!');
  app.quit();
  process.exit(0);
});
