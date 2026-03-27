const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let p2pProcess = null;

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    icon: path.join(__dirname, '../build/icon.png')
  });

  // 开发模式加载Vite开发服务器，生产模式加载构建后的文件
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
    // 关闭P2P进程
    if (p2pProcess) {
      p2pProcess.kill();
      p2pProcess = null;
    }
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// ==================== P2P进程管理 ====================

// 启动P2P节点
ipcMain.handle('p2p:start', async (event, config) => {
  try {
    if (p2pProcess) {
      throw new Error('P2P节点已在运行');
    }

    // 构建Python命令
    const pythonScript = path.join(__dirname, '../../ant coding/p2p/p2p_global.py');

    if (!fs.existsSync(pythonScript)) {
      throw new Error('P2P核心文件不存在，请先初始化项目');
    }

    p2pProcess = spawn('python', [pythonScript, JSON.stringify(config)], {
      cwd: path.join(__dirname, '../..'),
      stdio: ['pipe', 'pipe', 'pipe']
    });

    // 处理P2P进程输出
    p2pProcess.stdout.on('data', (data) => {
      console.log('P2P:', data.toString());
      // 解析输出并发送到前端
      const output = data.toString().trim();
      try {
        const lines = output.split('\n');
        lines.forEach(line => {
          if (line.startsWith('{') && line.endsWith('}')) {
            const message = JSON.parse(line);
            event.reply('p2p:message', message);
          }
        });
      } catch (e) {
        // 不是JSON，作为日志输出
        event.reply('p2p:log', { type: 'info', message: output });
      }
    });

    p2pProcess.stderr.on('data', (data) => {
      console.error('P2P Error:', data.toString());
      event.reply('p2p:log', { type: 'error', message: data.toString() });
    });

    p2pProcess.on('close', (code) => {
      console.log('P2P进程退出，代码:', code);
      p2pProcess = null;
      event.reply('p2p:stopped', { code });
    });

    return { success: true, message: 'P2P节点启动中...' };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 停止P2P节点
ipcMain.handle('p2p:stop', async () => {
  try {
    if (p2pProcess) {
      p2pProcess.kill();
      p2pProcess = null;
      return { success: true, message: 'P2P节点已停止' };
    } else {
      return { success: false, error: 'P2P节点未运行' };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 获取P2P状态
ipcMain.handle('p2p:status', async () => {
  return {
    running: p2pProcess !== null,
    pid: p2pProcess ? p2pProcess.pid : null
  };
});

// ==================== 邮件操作 ====================

// 发送邮件
ipcMain.handle('mail:send', async (event, data) => {
  try {
    // 这里会通过API服务器发送
    const response = await fetch('http://localhost:8102/api/send-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    return { success: result.success, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 获取收件箱
ipcMain.handle('mail:inbox', async () => {
  try {
    const response = await fetch('http://localhost:8102/api/inbox');
    const result = await response.json();
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 获取已发送
ipcMain.handle('mail:sent', async () => {
  try {
    const response = await fetch('http://localhost:8102/api/sent');
    const result = await response.json();
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// ==================== 联系人操作 ====================

// 添加联系人
ipcMain.handle('contact:add', async (event, contact) => {
  try {
    const response = await fetch('http://localhost:8102/api/contacts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(contact)
    });
    const result = await response.json();
    return { success: result.success, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// 获取联系人列表
ipcMain.handle('contact:list', async () => {
  try {
    const response = await fetch('http://localhost:8102/api/contacts');
    const result = await response.json();
    return { success: true, data: result };
  } catch (error) {
    return { success: false, error: error.message };
  }
});

// ==================== 文件操作 ====================

// 选择文件
ipcMain.handle('dialog:openFile', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile', 'multiSelections']
  });
  return result.canceled ? null : result.filePaths;
});

// 选择目录
ipcMain.handle('dialog:openDirectory', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory']
  });
  return result.canceled ? null : result.filePaths[0];
});
