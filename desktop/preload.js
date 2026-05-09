const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('mnLaserLab', {
  appVersion: () => ipcRenderer.invoke('app-version'),
  checkForUpdates: () => ipcRenderer.invoke('check-for-updates')
});
