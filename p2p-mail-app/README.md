# P2P SecureMail - 桌面应用

基于Electron + React的P2P加密邮件系统，端到端加密通信。

## 技术栈

- **前端**: React 18 + Vite + TailwindCSS
- **桌面**: Electron 28
- **后端**: Python (P2P核心)
- **状态管理**: Zustand
- **加密**: X25519 + ChaCha20-Poly1305

## 快速开始

### 1. 安装依赖

```bash
cd p2p-mail-app
npm install
```

### 2. 启动开发环境

```bash
npm run dev
```

这会同时启动:
- Vite开发服务器 (http://localhost:5173)
- Electron窗口 (热重载)

### 3. 打包发布

```bash
# 构建前端
npm run build

# 打包Electron应用
npm run build:electron
```

生成的安装包在 `dist-electron/` 目录。

## 项目结构

```
p2p-mail-app/
├── electron/          # Electron主进程
│   ├── main.js       # 主进程代码
│   └── preload.js    # 预加载脚本
├── src/
│   ├── components/   # React组件
│   ├── pages/        # 页面组件
│   ├── store/        # 状态管理
│   ├── utils/        # 工具函数
│   ├── App.jsx       # 根组件
│   └── main.jsx      # 入口文件
├── index.html       # HTML模板
├── package.json     # 项目配置
└── vite.config.js   # Vite配置
```

## 功能特性

### 已实现
- [x] 仪表盘
- [x] 收件箱
- [x] 已发送
- [x] 写邮件
- [x] 联系人管理
- [x] 设置页面
- [x] 端到端加密
- [x] P2P通信

### 开发中
- [ ] SQLite数据库
- [ ] 文件传输
- [ ] 消息状态
- [ ] 搜索功能
- [ ] 主题切换

## API接口

### P2P操作
```javascript
// 启动P2P节点
await window.electronAPI.p2p.start({ port: 8100 });

// 停止P2P节点
await window.electronAPI.p2p.stop();

// 获取状态
const status = await window.electronAPI.p2p.status();
```

### 邮件操作
```javascript
// 发送邮件
await window.electronAPI.mail.send({
  recipient_id: '...',
  subject: 'Hello',
  body: 'Message'
});

// 获取收件箱
const inbox = await window.electronAPI.mail.inbox();

// 获取已发送
const sent = await window.electronAPI.mail.sent();
```

### 联系人操作
```javascript
// 添加联系人
await window.electronAPI.contact.add({
  name: 'Alice',
  node_id: '...',
  group: '工作'
});

// 获取联系人列表
const contacts = await window.electronAPI.contact.list();
```

## 配置

### 网络配置
```javascript
{
  port: 8100,           // 本地端口
  stun_enabled: false,   // 是否启用STUN
  turn_servers: []       // TURN服务器列表
}
```

### 加密配置
```javascript
{
  key_exchange: 'X25519',      // 密钥交换算法
  encryption: 'ChaCha20-Poly1305',  // 加密算法
  key_length: 256                // 密钥长度(位)
}
```

## 故障排查

### P2P节点启动失败
1. 检查端口是否被占用: `netstat -ano | findstr :8100`
2. 检查Python环境: `python --version`
3. 查看日志: `electron/log/`

### 界面不显示
1. 检查Vite是否启动: 访问 http://localhost:5173
2. 检查Electron日志: 打开开发者工具 (Ctrl+Shift+I)

### 邮件发送失败
1. 检查接收方是否在线
2. 检查是否已交换公钥
3. 检查防火墙设置

## 开发路线图

### Phase 1 (当前) - MVP
- [x] 基础界面
- [x] 邮件发送/接收
- [x] 联系人管理

### Phase 2 - 增强
- [ ] SQLite数据库
- [ ] 文件传输
- [ ] 搜索功能

### Phase 3 - 企业版
- [ ] 管理后台
- [ ] 批量操作
- [ ] API接口

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
