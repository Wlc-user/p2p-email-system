# P2P SecureMail - 桌面应用

**已完成MVP！可以立即使用！**

---

## 🚀 快速开始（2步）

### 1. 安装依赖
双击运行 `一键启动完整版.bat`

或者手动执行：
```bash
cd p2p-mail-app
npm install
```

### 2. 启动应用
脚本会自动：
- ✅ 启动Python API服务器（端口8102）
- ✅ 启动Electron + React应用
- ✅ 自动打开浏览器窗口

---

## 📋 功能清单

### ✅ 已完成
- [x] Electron + React 框架
- [x] 6个核心页面（仪表盘、收件箱、已发送、写邮件、联系人、设置）
- [x] Python API服务器
- [x] SQLite数据库
- [x] 端到端加密（X25519 + ChaCha20-Poly1305）
- [x] P2P通信
- [x] API测试页面

### 🔄 开发中
- [ ] 文件传输
- [ ] 消息状态
- [ ] 搜索功能

---

## 🎯 使用指南

### 第1次使用
1. 双击 `一键启动完整版.bat`
2. 等待应用启动（约5秒）
3. 点击左侧 **API测试** 按钮
4. 运行所有测试，确保连接正常

### 写邮件
1. 点击 **写邮件**
2. 输入接收方的节点ID（40位）
3. 编写主题和正文
4. 点击 **发送邮件**

### 查看收件箱
1. 点击 **收件箱**
2. 点击邮件查看详情
3. 可以回复、转发、删除

### 管理联系人
1. 点击 **联系人**
2. 点击 **添加联系人**
3. 填写名称和节点ID
4. 可以设置分组（如：工作、家庭）

### 查看设置
1. 点击 **设置**
2. 配置网络端口
3. 查看加密算法信息
4. 管理存储数据

---

## 🔧 API接口

### P2P操作
```javascript
// 健康检查
GET http://localhost:8102/api/health

// 启动P2P节点
POST http://localhost:8102/api/start
Body: { port: 8100, seed: "user@localhost" }

// 停止P2P节点
POST http://localhost:8102/api/stop

// 获取节点信息
GET http://localhost:8102/api/node
```

### 邮件操作
```javascript
// 发送邮件
POST http://localhost:8102/api/send-email
Body: {
  recipient_id: "40位节点ID",
  subject: "主题",
  body: "正文"
}

// 获取收件箱
GET http://localhost:8102/api/inbox

// 获取已发送
GET http://localhost:8102/api/sent
```

### 联系人操作
```javascript
// 添加联系人
POST http://localhost:8102/api/contacts
Body: {
  name: "Alice",
  node_id: "40位节点ID",
  group: "工作"
}

// 获取联系人列表
GET http://localhost:8102/api/contacts
```

---

## 📊 项目结构

```
ant-coding-main/
├── p2p-mail-app/              # Electron应用
│   ├── electron/              # Electron主进程
│   │   ├── main.js           # 主进程代码
│   │   └── preload.js        # 预加载脚本
│   ├── src/
│   │   ├── components/       # React组件
│   │   │   ├── Layout.jsx
│   │   │   └── P2PStatus.jsx
│   │   ├── pages/            # 页面
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Inbox.jsx
│   │   │   ├── Sent.jsx
│   │   │   ├── Compose.jsx
│   │   │   ├── Contacts.jsx
│   │   │   ├── Settings.jsx
│   │   │   └── TestAPI.jsx
│   │   ├── store/            # 状态管理
│   │   │   └── p2p.js
│   │   ├── utils/            # 工具函数
│   │   │   └── cn.js
│   │   ├── App.jsx           # 根组件
│   │   └── main.jsx          # 入口文件
│   ├── index.html
│   ├── package.json
│   └── README.md
│
├── ant coding/p2p/          # P2P核心
│   ├── p2p_global.py        # 核心实现（包含API服务）
│   ├── test_p2p_global.py   # 测试脚本
│   └── TEST_REPORT.md       # 测试报告
│
└── mailbox/                  # 数据存储
    ├── p2p_mail.db          # SQLite数据库
    └── <node_id>/          # 邮件文件
```

---

## 🐛 故障排查

### 应用无法启动
1. 检查Node.js是否安装: `node --version`
2. 检查端口8102是否被占用: `netstat -ano | findstr :8102`
3. 删除 `node_modules` 重新安装

### API测试失败
1. 检查Python API服务器是否运行
2. 访问 http://localhost:8102/api/health
3. 查看Python日志输出

### 邮件发送失败
1. 检查P2P节点是否启动
2. 检查是否已与对方交换公钥
3. 检查对方节点是否在线

---

## 📦 打包发布

### Windows
```bash
cd p2p-mail-app
npm run build
npm run build:electron
```
生成: `dist-electron/p2p-secure-mail Setup.exe`

### Mac
```bash
cd p2p-mail-app
npm run build
npm run build:electron
```
生成: `dist-electron/p2p-secure-mail.dmg`

### Linux
```bash
cd p2p-mail-app
npm run build
npm run build:electron
```
生成: `dist-electron/p2p-secure-mail.AppImage`

---

## 🎯 下一步

### 短期（1周）
- [ ] 完善错误处理
- [ ] 添加更多测试
- [ ] 优化UI/UX

### 中期（1个月）
- [ ] 文件传输功能
- [ ] 消息状态追踪
- [ ] 搜索功能

### 长期（3个月）
- [ ] 移动端App
- [ ] 云中继服务
- [ ] 企业版功能

---

## 📞 技术支持

### 文档
- GitHub: [项目地址]
- Wiki: 详细文档

### 问题反馈
- Issue: 提交Bug
- Discussion: 参与讨论

---

## 🎉 开始使用吧！

**双击 `一键启动完整版.bat`，立即开始使用P2P加密邮件系统！**

---

**注意**:
- 这是MVP版本，功能持续更新中
- 所有数据存储在本地
- 端到端加密，只有收发双方能查看邮件

---

**版本**: 1.0.0
**协议**: MIT License
**开发**: 独立开发者
