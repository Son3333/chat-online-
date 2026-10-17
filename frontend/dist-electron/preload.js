"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const electron_1 = require("electron");
const api = {
    sendRequest: (action, payload = {}) => {
        return electron_1.ipcRenderer.invoke('python:request', { action, payload });
    },
    onServerEvent: (callback) => {
        const handler = (_event, data) => callback(data);
        electron_1.ipcRenderer.on('server:event', handler);
        return () => {
            electron_1.ipcRenderer.removeListener('server:event', handler);
        };
    },
    onUpdateAvailable: (callback) => {
        const handler = (_event, data) => callback(data);
        electron_1.ipcRenderer.on('app:update_available', handler);
        return () => {
            electron_1.ipcRenderer.removeListener('app:update_available', handler);
        };
    },
    applyUpdate: () => electron_1.ipcRenderer.invoke('app:apply_update'),
    checkUpdateNow: () => electron_1.ipcRenderer.invoke('app:check_update'),
    getServerInfo: () => electron_1.ipcRenderer.invoke('app:get-server-info'),
    getServerConfig: () => electron_1.ipcRenderer.invoke('app:get-server-config'),
    setServerConfig: (config) => electron_1.ipcRenderer.invoke('app:set-server-config', config),
    getScreenSourceId: () => electron_1.ipcRenderer.invoke('media:get-screen-source-id'),
    openExternal: (url) => electron_1.ipcRenderer.invoke('app:open-external', url),
    minimizeWindow: () => electron_1.ipcRenderer.send('window:minimize'),
    maximizeWindow: () => electron_1.ipcRenderer.send('window:maximize'),
    closeWindow: () => electron_1.ipcRenderer.send('window:close'),
    setAlwaysOnTop: (enabled) => electron_1.ipcRenderer.invoke('window:set-always-on-top', enabled),
    isAlwaysOnTop: () => electron_1.ipcRenderer.invoke('window:is-always-on-top'),
    selectLocalFile: (category) => electron_1.ipcRenderer.invoke('dialog:select-file', category),
    saveDownloadedFile: (fileName, base64Data) => electron_1.ipcRenderer.invoke('dialog:save-file', { fileName, base64Data }),
};
electron_1.contextBridge.exposeInMainWorld('api', api);
