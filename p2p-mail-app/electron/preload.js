const { contextBridge, ipcRenderer } = require('electron');

// 暴露安全的API给渲染进程
contextBridge.exposeInMainWorld('electronAPI', {
  // P2P操作
  p2p: {
    start: (config) => ipcRenderer.invoke('p2p:start', config),
    stop: () => ipcRenderer.invoke('p2p:stop'),
    status: () => ipcRenderer.invoke('p2p:status'),
    onMessage: (callback) => ipcRenderer.on('p2p:message', (event, data) => callback(data)),
    onLog: (callback) => ipcRenderer.on('p2p:log', (event, data) => callback(data)),
    onStopped: (callback) => ipcRenderer.on('p2p:stopped', (event, data) => callback(data))
  },

  // 邮件操作
  mail: {
    send: (data) => ipcRenderer.invoke('mail:send', data),
    inbox: () => ipcRenderer.invoke('mail:inbox'),
    sent: () => ipcRenderer.invoke('mail:sent')
  },

  // 联系人操作
  contact: {
    add: (contact) => ipcRenderer.invoke('contact:add', contact),
    list: () => ipcRenderer.invoke('contact:list')
  },

  // 对话框
  dialog: {
    openFile: () => ipcRenderer.invoke('dialog:openFile'),
    openDirectory: () => ipcRenderer.invoke('dialog:openDirectory')
  }
});
