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

  // --- 1. DIRECT CHAT VỚI PHẠM ĐỨC TÂM TRƯỚC KHI ĐẶT BIỆT DANH ---
  console.log('[Capture] 1. Resetting direct nickname to null (Before)...');
  await pythonBridge.sendRequest('set_conversation_nickname', {
    conversation_id: 1,
    user_id: 2844831592,
    target_user_id: 7217665131,
    nickname: ''
  });
  await sleep(600);

  console.log('[Capture] 1. Selecting Direct Chat with Pham Duc Tam...');
  await mainWindow.webContents.executeJavaScript(`
    const items = Array.from(document.querySelectorAll('aside div.cursor-pointer'));
    const directUser = items.find(el => el.textContent.includes('Pham Duc Tam'));
    if (directUser) directUser.click();
  `);
  await sleep(2000);
  await snap('3_before_direct_nickname.png');

  // Mở menu tùy chọn khác -> Đặt biệt danh
  console.log('[Capture] 2. Opening Nickname Modal...');
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

  // Đặt biệt danh: "Tâm Bạn Thân (KTPM)"
  console.log('[Capture] 3. Setting Nickname Tâm Bạn Thân (KTPM)...');
  await mainWindow.webContents.executeJavaScript(`
    const input = document.querySelector('input[placeholder*="biệt danh"]');
    if (input) {
      input.value = 'Tâm Bạn Thân (KTPM)';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const saveBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Lưu biệt danh'));
    if (saveBtn) saveBtn.click();
  `);
  await sleep(2000);
  await snap('3_after_direct_nickname.png');

  // --- 4. CẬP NHẬT ẢNH ĐẠI DIỆN VÀ TÊN NHÓM ---
  console.log('[Capture] 4. Updating Group Avatar and Name...');
  // Đọc file logo.png làm avatar nhóm
  const logoBuf = fs.readFileSync(path.resolve(__dirname, '..', 'frontend', 'src', 'assets', 'logo.png'));
  const logoBase64 = `data:image/png;base64,${logoBuf.toString('base64')}`;

  await pythonBridge.sendRequest('update_group_info', {
    conversation_id: 12,
    user_id: 2844831592,
    title: 'Nhóm Đồ Án KTPM (VIP)',
    avatar_url: logoBase64
  });
  await sleep(1000);

  // Click vào nhóm để hiển thị header và sidebar có avatar nhóm mới!
  await mainWindow.webContents.executeJavaScript(`
    const items = Array.from(document.querySelectorAll('aside div.cursor-pointer'));
    const group = items.find(el => el.textContent.includes('Nhóm') || el.textContent.includes('VIP'));
    if (group) group.click();
  `);
  await sleep(2000);
  await snap('2_after_group_avatar_in_chat.png');

  // Mở modal thông tin nhóm để xem avatar nhóm lớn và danh sách thành viên
  await mainWindow.webContents.executeJavaScript(`
    const infoBtn = document.querySelector('button[title="Xem thông tin hội thoại"]') || document.querySelector('div[title="Xem thông tin hội thoại"]');
    if (infoBtn) infoBtn.click();
  `);
  await sleep(2000);
  await snap('2_after_group_info_modal.png');

  console.log('[Capture] COMPLETED ALL NICKNAME & GROUP AVATAR SCREENSHOTS!');
  app.quit();
  process.exit(0);
});
