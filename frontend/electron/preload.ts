import { contextBridge, ipcRenderer } from 'electron';

export interface ElectronAPI {
  sendRequest: (action: string, payload?: Record<string, any>) => Promise<any>;
  onServerEvent: (callback: (event: any) => void) => () => void;
  minimizeWindow: () => void;
  maximizeWindow: () => void;
  closeWindow: () => void;
  setAlwaysOnTop: (enabled: boolean) => Promise<boolean>;
  isAlwaysOnTop: () => Promise<boolean>;
  selectLocalFile: () => Promise<{ canceled: boolean; fileName?: string; fileData?: string; fileSize?: number }>;
  saveDownloadedFile: (fileName: string, base64Data: string) => Promise<{ success: boolean; path?: string }>;
  onUpdateAvailable: (callback: (updateInfo: { remoteHash: string; localHash: string; message: string }) => void) => () => void;
  applyUpdate: () => Promise<{ success: boolean; error?: string }>;
  checkUpdateNow: () => Promise<any>;
  getServerInfo: () => Promise<{ isWan: boolean; address: string }>;
}

const api: ElectronAPI = {
  sendRequest: (action, payload = {}) => {
    return ipcRenderer.invoke('python:request', { action, payload });
  },
  onServerEvent: (callback) => {
    const handler = (_event: any, data: any) => callback(data);
    ipcRenderer.on('server:event', handler);
    return () => {
      ipcRenderer.removeListener('server:event', handler);
    };
  },
  onUpdateAvailable: (callback) => {
    const handler = (_event: any, data: any) => callback(data);
    ipcRenderer.on('app:update_available', handler);
    return () => {
      ipcRenderer.removeListener('app:update_available', handler);
    };
  },
  applyUpdate: () => ipcRenderer.invoke('app:apply_update'),
  checkUpdateNow: () => ipcRenderer.invoke('app:check_update'),
  getServerInfo: () => ipcRenderer.invoke('app:get-server-info'),
  minimizeWindow: () => ipcRenderer.send('window:minimize'),
  maximizeWindow: () => ipcRenderer.send('window:maximize'),
  closeWindow: () => ipcRenderer.send('window:close'),
  setAlwaysOnTop: (enabled) => ipcRenderer.invoke('window:set-always-on-top', enabled),
  isAlwaysOnTop: () => ipcRenderer.invoke('window:is-always-on-top'),
  selectLocalFile: () => ipcRenderer.invoke('dialog:select-file'),
  saveDownloadedFile: (fileName, base64Data) => ipcRenderer.invoke('dialog:save-file', { fileName, base64Data }),
};

contextBridge.exposeInMainWorld('api', api);

