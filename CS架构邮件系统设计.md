# CS 架构邮件系统设计文档

## 为什么选择 CS 架构？

### 对比分析

| 特性 | P2P 架构 | CS 架构 |
|------|-----------|---------|
| **实现复杂度** | 高（NAT穿透、节点发现） | 低（标准HTTP API） |
| **可靠性** | 低（依赖双方在线） | 高（服务器持久存储） |
| **消息投递** | 需要双方同时在线 | 离线也能接收 |
| **数据同步** | 复杂（分布式同步） | 简单（中心数据库） |
| **扩展性** | 差（网络拓扑复杂） | 好（水平扩展） |
| **加密通信** | 端到端 | 端到端（可选） |
| **适用场景** | 小型测试网络 | 生产环境、企业应用 |

### 优势

**CS 架构的优势：**
1. ✅ **简单可靠** - 标准的客户端-服务器模型
2. ✅ **离线支持** - 消息存储在服务器
3. ✅ **易于部署** - 部署在任何云服务器
4. ✅ **高可用性** - 服务器宕机有多个备份方案
5. ✅ **监控维护** - 集中式日志和监控
6. ✅ **数据管理** - 中心化数据库，易于备份

**仍然保持的优势：**
1. ✅ **端到端加密** - 服务器无法查看内容
2. ✅ **用户隐私** - 只需要用户ID，不需要真实身份
3. ✅ **去中心化标识** - 节点ID作为唯一标识
4. ✅ **现代UI** - React 前端界面

---

## 系统架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                  客户端 (React)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  收件箱  │  │  已发送  │  │ 写邮件   │   │
│  └──────────┘  └──────────┘  └──────────┘   │
│         │             │              │            │
│         └─────────────┴──────────────┘            │
│                    │ HTTPS / REST API            │
└────────────────────┼───────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              邮件服务器 (Python/Flask)            │
│  ┌────────────────────────────────────────┐         │
│  │          REST API 层                │         │
│  │  - /api/register                   │         │
│  │  - /api/login                      │         │
│  │  - /api/emails/inbox              │         │
│  │  - /api/emails/send              │         │
│  │  - /api/contacts                 │         │
│  └────────────────────────────────────────┘         │
│         │                                  │
│  ┌──────┴───────┐  ┌─────────────────┐  │
│  │  业务逻辑层   │  │   加密模块     │  │
│  │  - 邮件处理  │  │  - ECDH密钥   │  │
│  │  - 联系人管理 │  │  - ChaCha20   │  │
│  │  - 用户认证   │  │  - 端到端加密 │  │
│  └──────┬───────┘  └─────────────────┘  │
│         │                                  │
│  ┌──────┴───────┐  ┌─────────────────┐  │
│  │  数据访问层  │  │   缓存层      │  │
│  │  - SQL查询   │  │  - Redis      │  │
│  │  - 数据映射  │  │  - 会话缓存  │  │
│  └──────┬───────┘  └─────────────────┘  │
│         │                                  │
│  ┌──────┴──────────────────────────────┐  │
│  │     数据库 (SQLite/PostgreSQL)     │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 技术栈选择

### 后端技术栈

**核心框架：**
- **Flask** - 轻量级 Python Web 框架
  - 简单易用
  - 丰富的扩展
  - 适合快速开发

**数据库：**
- **SQLite**（开发/小型部署）
  - 零配置
  - 单文件存储
  - 适合演示

- **PostgreSQL**（生产环境，可选）
  - 高性能
  - 支持并发
  - 适合大规模

**加密库：**
- **cryptography** - Python 标准加密库
  - X25519 密钥交换
  - ChaCha20-Poly1305 加密
  - 标准化实现

**其他组件：**
- **SQLAlchemy** - ORM 框架
- **PyJWT** - JWT 认证
- **Flask-CORS** - 跨域支持
- **Gunicorn** - WSGI 服务器

### 前端技术栈

- **React 18** - UI 框架
- **Vite** - 构建工具
- **React Router** - 路由
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库
- **Tailwind CSS** - 样式

---

## 数据库设计

### 表结构

#### 1. users（用户表）
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id VARCHAR(40) UNIQUE NOT NULL,  -- 节点ID（用户标识）
    username VARCHAR(50) UNIQUE,             -- 用户名（可选）
    public_key TEXT NOT NULL,                -- 公钥（用于加密）
    password_hash VARCHAR(255),                -- 密码哈希（可选）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. emails（邮件表）
```sql
CREATE TABLE emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id VARCHAR(64) UNIQUE NOT NULL,
    sender_id VARCHAR(40) NOT NULL,         -- 发送者节点ID
    recipient_id VARCHAR(40) NOT NULL,      -- 接收者节点ID
    subject VARCHAR(255) NOT NULL,
    encrypted_body TEXT NOT NULL,             -- 加密的邮件内容
    nonce VARCHAR(32) NOT NULL,             -- 加密nonce
    read_status BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(node_id),
    FOREIGN KEY (recipient_id) REFERENCES users(node_id)
);
```

#### 3. contacts（联系人表）
```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(40) NOT NULL,           -- 所属用户
    contact_node_id VARCHAR(40) NOT NULL,      -- 联系人节点ID
    contact_name VARCHAR(100),                -- 联系人名称
    contact_public_key TEXT,                   -- 联系人公钥
    group_name VARCHAR(50) DEFAULT '未分组',   -- 分组
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(node_id),
    UNIQUE(user_id, contact_node_id)
);
```

#### 4. encryption_keys（加密密钥表）
```sql
CREATE TABLE encryption_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(40) NOT NULL,
    peer_id VARCHAR(40) NOT NULL,
    shared_secret TEXT NOT NULL,              -- 共享密钥（加密存储）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(node_id),
    FOREIGN KEY (peer_id) REFERENCES users(node_id),
    UNIQUE(user_id, peer_id)
);
```

---

## API 设计

### 认证相关

#### POST /api/register
注册新用户

**请求：**
```json
{
  "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
  "username": "张三",
  "password": "password123"
}
```

**响应：**
```json
{
  "success": true,
  "message": "注册成功",
  "user": {
    "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
    "public_key": "-----BEGIN PUBLIC KEY-----...",
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

#### POST /api/login
用户登录

**请求：**
```json
{
  "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
  "password": "password123"
}
```

**响应：**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
    "username": "张三"
  }
}
```

### 邮件相关

#### GET /api/emails/inbox
获取收件箱

**请求头：**
```
Authorization: Bearer <token>
```

**响应：**
```json
{
  "success": true,
  "emails": [
    {
      "id": 1,
      "message_id": "abc123...",
      "sender_id": "fedcba0987654321098765432109876543210fed",
      "sender_name": "李四",
      "subject": "你好",
      "encrypted_body": "base64encrypted...",
      "nonce": "base64nonce...",
      "read_status": false,
      "created_at": "2025-01-01T10:00:00Z"
    }
  ]
}
```

#### GET /api/emails/sent
获取已发送邮件

#### GET /api/emails/{message_id}
获取单封邮件

#### POST /api/emails/send
发送邮件

**请求：**
```json
{
  "recipient_id": "fedcba0987654321098765432109876543210fed",
  "subject": "你好",
  "body": "这是一封测试邮件"
}
```

**响应：**
```json
{
  "success": true,
  "message_id": "xyz789...",
  "message": "邮件发送成功"
}
```

### 联系人相关

#### GET /api/contacts
获取联系人列表

#### POST /api/contacts
添加联系人

**请求：**
```json
{
  "contact_node_id": "fedcba0987654321098765432109876543210fed",
  "contact_name": "李四",
  "group_name": "同事"
}
```

#### DELETE /api/contacts/{id}
删除联系人

### 公钥相关

#### GET /api/publickey/{node_id}
获取用户公钥

**响应：**
```json
{
  "success": true,
  "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
  "public_key": "-----BEGIN PUBLIC KEY-----..."
}
```

---

## 加密流程

### 1. 用户注册时生成密钥对

```python
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

# 生成密钥对
private_key = x25519.X25519PrivateKey.generate()
public_key = private_key.public_key()

# 导出公钥
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)

# 保存到数据库
user.public_key = base64.b64encode(public_bytes).decode()
user.private_key = base64.b64encode(
    private_key.private_bytes(...)
).decode()
```

### 2. 发送邮件时加密

```python
# 1. 获取接收者公钥
recipient = db.get_user(recipient_id)
recipient_public_key = x25519.X25519PublicKey.from_public_bytes(
    base64.b64decode(recipient.public_key)
)

# 2. 计算共享密钥
shared_secret = my_private_key.exchange(recipient_public_key)

# 3. 使用 ChaCha20-Poly1305 加密
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import hashlib
import os

key = hashlib.sha256(shared_secret).digest()[:32]
nonce = os.urandom(12)
chacha = ChaCha20Poly1305(key)

encrypted = chacha.encrypt(nonce, plaintext.encode(), None)

# 4. 保存到数据库
email = {
    'message_id': generate_message_id(),
    'sender_id': my_node_id,
    'recipient_id': recipient_id,
    'encrypted_body': base64.b64encode(encrypted).decode(),
    'nonce': base64.b64encode(nonce).decode()
}
```

### 3. 接收邮件时解密

```python
# 1. 获取共享密钥
shared_secret = my_private_key.exchange(
    sender_public_key
)

# 2. 解密邮件
key = hashlib.sha256(shared_secret).digest()[:32]
chacha = ChaCha20Poly1305(key)

ciphertext = base64.b64decode(email.encrypted_body)
nonce = base64.b64decode(email.nonce)

plaintext = chacha.decrypt(nonce, ciphertext, None)
```

---

## 前端修改

### 1. 认证模块

```javascript
// auth.js
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export const authService = {
  async register(nodeId, username, password) {
    const response = await axios.post(`${API_URL}/register`, {
      node_id: nodeId,
      username,
      password
    });
    return response.data;
  },

  async login(nodeId, password) {
    const response = await axios.post(`${API_URL}/login`, {
      node_id: nodeId,
      password
    });
    const { token } = response.data;
    localStorage.setItem('auth_token', token);
    return response.data;
  },

  logout() {
    localStorage.removeItem('auth_token');
  },

  getToken() {
    return localStorage.getItem('auth_token');
  },

  getHeaders() {
    return {
      'Authorization': `Bearer ${this.getToken()}`
    };
  }
};
```

### 2. API 客户端

```javascript
// api.js
import axios from 'axios';
import { authService } from './auth';

const API_URL = 'http://localhost:5000/api';

export const emailAPI = {
  async getInbox() {
    const response = await axios.get(
      `${API_URL}/emails/inbox`,
      { headers: authService.getHeaders() }
    );
    return response.data.emails;
  },

  async sendEmail(recipientId, subject, body) {
    // 1. 获取接收者公钥
    const pubkeyResponse = await axios.get(
      `${API_URL}/publickey/${recipientId}`
    );

    // 2. 在前端加密（端到端）
    const encrypted = await encryptMessage(
      body,
      pubkeyResponse.data.public_key
    );

    // 3. 发送加密邮件
    const response = await axios.post(
      `${API_URL}/emails/send`,
      {
        recipient_id: recipientId,
        subject,
        encrypted_body: encrypted.ciphertext,
        nonce: encrypted.nonce
      },
      { headers: authService.getHeaders() }
    );

    return response.data;
  }
};
```

---

## 部署方案

### 开发环境

```bash
# 后端
cd backend
python app.py

# 前端
cd frontend
npm run dev
```

### 生产环境

**后端部署：**
```bash
# 使用 Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 或使用 uWSGI
uwsgi --http 0.0.0.0:5000 --wsgi-file app.py
```

**前端部署：**
```bash
# 构建
npm run build

# 使用 nginx
server {
    listen 80;
    server_name mail.example.com;

    location / {
        root /var/www/mail/dist;
        try_files $uri /index.html;
    }
}
```

---

## 安全考虑

### 1. 端到端加密

- ✅ 服务器无法查看邮件内容
- ✅ 只有发送者和接收者能解密
- ✅ 数据库泄露也安全

### 2. 认证和授权

- ✅ JWT token 认证
- ✅ 请求签名验证
- ✅ 密码哈希存储（bcrypt）

### 3. 传输安全

- ✅ 强制 HTTPS
- ✅ TLS 1.3
- ✅ 证书验证

### 4. 数据保护

- ✅ 敏感数据加密存储
- ✅ 定期备份
- ✅ 访问日志审计

---

## 迁移计划

### 阶段1：后端开发（3-5天）
- [ ] 搭建 Flask 项目结构
- [ ] 实现数据库模型
- [ ] 实现 REST API
- [ ] 实现加密模块

### 阶段2：前端适配（2-3天）
- [ ] 添加认证页面
- [ ] 更新 API 调用
- [ ] 实现前端加密
- [ ] 测试端到端加密

### 阶段3：测试优化（2-3天）
- [ ] 单元测试
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档完善

### 阶段4：部署上线（1-2天）
- [ ] 配置生产环境
- [ ] 部署服务器
- [ ] 配置域名和证书
- [ ] 监控和日志

---

## 总结

### CS 架构的优势

| 方面 | 优势 |
|------|------|
| **可靠性** | 高，服务器持久存储 |
| **可用性** | 离线也能接收邮件 |
| **扩展性** | 易于水平扩展 |
| **维护性** | 集中式监控和日志 |
| **开发效率** | 标准Web开发流程 |
| **部署简单** | 部署在任何云服务器 |

### 保持的隐私特性

虽然使用CS架构，但仍然保持：
1. ✅ **端到端加密** - 服务器无法查看邮件
2. ✅ **匿名标识** - 使用节点ID而非真实身份
3. ✅ **用户控制** - 用户控制自己的密钥

### 适用场景

CS 架构适合：
- ✅ 生产环境邮件系统
- ✅ 企业内部通信
- ✅ 隐私邮件服务
- ✅ 加密聊天应用

不适用场景：
- ❌ 完全去中心化系统
- ❌ 无服务器架构
- ❌ 区块链应用
