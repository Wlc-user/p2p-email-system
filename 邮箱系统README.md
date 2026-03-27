# 企业级CS架构邮箱系统

一个完整的、可测试的、有安全设计的客户端-服务器(CS)架构邮件系统。

## 📋 项目概述

本系统实现了完整的邮件功能,包括双域名支持、端到端加密、智能防护等特性,满足生产环境部署要求。

### ✨ 核心特性

- **双域名支持** - 两个独立邮件系统可互发邮件
- **端到端加密** - X25519 ECDH + ChaCha20-Poly1305 加密
- **安全防护** - 登录防爆、发送限流、垃圾邮件识别
- **邮件撤回** - 5分钟内可撤回已发送邮件
- **附件支持** - 图片附件发送与读取
- **群发功能** - 批量发送邮件
- **智能功能** - 快捷回复推荐、快捷操作提取
- **并发稳定** - 支持多客户端同时访问

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install flask flask-cors cryptography requests
```

### 2. 启动系统

```bash
# Windows 一键启动
快速启动.bat

# 或手动启动双服务器
python mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001
python mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002
```

### 3. 运行测试

```bash
python test_mail_system.py
```

## 📁 项目结构

```
mail-system/
├── mail_server.py              # 核心服务器(支持双域名)
├── test_mail_system.py         # 完整测试套件
├── 快速启动.bat                 # 一键启动脚本
├── start_dual_servers.bat      # 双服务器启动
├── start_client.bat            # 客户端启动
├── server_a_data/              # 服务器A数据库
├── server_b_data/              # 服务器B数据库
├── 邮箱系统部署指南.md          # 详细部署文档
└── 邮箱系统测试报告.md          # 测试结果报告
```

## 🎯 功能清单

### 服务器管理

- ✅ 实现server进程,负责接收、存储、分发邮件
- ✅ 同时运行两个服务器(模拟两个隔离域名)
- ✅ 两个系统之间可互相发信
- ✅ 存储逻辑隔离(独立数据库)

### 客户端管理

- ✅ 注册/登录(用户名、密码、确认密码)
- ✅ 写邮件、收件箱、发件箱、草稿箱
- ✅ 群发与群组管理
- ✅ 快速回复(自动补全、快捷推荐)
- ✅ 图片附件发送与读取
- ✅ 邮件撤回(5分钟内)
- ✅ 邮件快捷操作(日历、待办、链接)

### 算法增强功能

- ✅ 垃圾邮件识别(基于关键词和模式)
- ✅ 快捷回复推荐(基于邮件内容)

### 安全与稳定性

- ✅ 用户登录后的安全交互(端到端加密)
- ✅ 登录防爆破(限流、封禁)
- ✅ 客户端防滥发/DOS基础防护
- ✅ 账户敏感信息保护(密码哈希)
- ✅ 初级钓鱼/垃圾邮件识别
- ✅ 撤回邮件核验(身份、时间、状态验证)

## 🔒 安全设计

### 端到端加密

```python
# 密钥交换: X25519 ECDH
# 对称加密: ChaCha20-Poly1305
# 密钥派生: PBKDF2 (100000次迭代)
```

**安全性保证:**
- 服务器无法查看邮件内容
- 数据库泄露也安全
- 只有发送者和接收者可解密

### 登录防爆

- 同一IP 5次失败后封禁15分钟
- 密码错误不返回具体提示
- PBKDF2哈希存储(100000次迭代)

### 发送限流

- 每小时最多发送50封邮件
- 每分钟最多发送5封邮件
- IP级别封禁

### 垃圾邮件识别

- 关键词匹配(中奖、优惠等)
- 标题全大写检测
- 多个感叹号检测
- 可疑URL模式检测

## 🧪 测试覆盖

### 测试用例(10项)

1. ✅ 基本功能(注册、登录、发送、接收)
2. ✅ 跨域通信(双服务器互发)
3. ✅ 安全防护(限流、垃圾识别)
4. ✅ 密码保护(哈希、防爆)
5. ✅ 邮件撤回(时间限制、身份核验)
6. ✅ 智能功能(快捷回复、操作提取)
7. ✅ 并发操作(10用户并发)
8. ✅ 附件功能(图片收发)
9. ✅ 群发功能(批量发送)
10. ✅ 跨域隔离(数据独立)

### 测试结果

```
============================================================
测试总结
============================================================
✓ 通过: 10/10
✗ 失败: 0/10

✓ 所有测试通过!
============================================================
```

## 📡 API 接口

### 认证相关

```http
POST /api/register          # 用户注册
POST /api/login             # 用户登录
GET  /api/publickey/:id     # 获取公钥
```

### 邮件相关

```http
GET    /api/emails/inbox           # 获取收件箱
GET    /api/emails/sent            # 获取已发送
GET    /api/emails/drafts          # 获取草稿箱
POST   /api/emails/send            # 发送邮件
POST   /api/emails/drafts          # 保存草稿
POST   /api/emails/:id/recall      # 撤回邮件
POST   /api/emails/:id/mark-read   # 标记已读
```

### 联系人相关

```http
GET    /api/contacts          # 获取联系人
POST   /api/contacts          # 添加联系人
DELETE /api/contacts/:id      # 删除联系人
```

### 群组相关

```http
GET    /api/groups            # 获取群组
POST   /api/groups            # 创建群组
```

### 智能分析

```http
POST /api/analyze/spam          # 分析垃圾邮件
POST /api/analyze/quick-replies # 推荐快捷回复
POST /api/analyze/quick-actions # 提取快捷操作
```

### 健康检查

```http
GET /api/health             # 健康检查
```

## 💻 使用示例

### 注册用户

```bash
curl -X POST http://localhost:5001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
    "username": "Alice",
    "password": "password123",
    "confirm_password": "password123"
  }'
```

### 发送邮件

```bash
curl -X POST http://localhost:5001/api/emails/send \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "recipient_id": "fedcba0987654321098765432109876543210fed",
    "subject": "你好",
    "encrypted_body": "BASE64_ENCRYPTED_CONTENT",
    "nonce": "BASE64_NONCE"
  }'
```

### 分析垃圾邮件

```bash
curl -X POST http://localhost:5001/api/analyze/spam \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "恭喜您中奖了",
    "body": "点击领取100万大奖"
  }'
```

## 🛠 部署指南

### 开发环境

```bash
# 启动双服务器
快速启动.bat

# 或手动启动
python mail_server.py --db-path server_a_data/mail.db --domain mail-a.com --port 5001
python mail_server.py --db-path server_b_data/mail.db --domain mail-b.com --port 5002
```

### 生产环境

**使用 Gunicorn:**
```bash
gunicorn -w 4 -b 0.0.0.0:5001 \
  --env DB_PATH=/data/server_a/mail.db \
  --env SERVER_DOMAIN=mail-a.com \
  mail_server:app
```

**使用 Nginx 反向代理:**
```nginx
upstream mail_a {
    server localhost:5001;
}

server {
    listen 80;
    server_name mail-a.com;

    location / {
        proxy_pass http://mail_a;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

详细部署指南请参考: [邮箱系统部署指南.md](./邮箱系统部署指南.md)

## 📊 技术栈

### 后端

- **Flask** - Web框架
- **SQLite** - 数据库(开发环境)
- **cryptography** - 加密库
- **requests** - HTTP客户端(测试)

### 加密算法

- **X25519** - ECDH密钥交换
- **ChaCha20-Poly1305** - 对称加密
- **PBKDF2-SHA256** - 密码哈希
- **Base64** - 数据编码

### 安全特性

- 端到端加密
- 登录防爆(限流+封禁)
- 发送限流(防DOS)
- 垃圾邮件识别
- 密码哈希存储

## 📝 文档

- [邮箱系统部署指南.md](./邮箱系统部署指南.md) - 详细部署和使用说明
- [邮箱系统测试报告.md](./邮箱系统测试报告.md) - 完整测试结果报告

## 🔍 故障排查

### 端口被占用

```bash
# 检查端口占用
netstat -ano | findstr :5001

# 更换端口
python mail_server.py --port 5003
```

### 数据库锁定

```bash
# 关闭所有服务器
taskkill /F /IM python.exe

# 检查数据库
sqlite3 email_system.db "PRAGMA integrity_check;"
```

### 跨域邮件失败

- 确保接收者在发送服务器有记录
- 检查两个服务器都正常运行
- 验证网络连接

## 📄 许可证

本项目仅供学习和研究使用。

## 👥 贡献

欢迎提出问题和改进建议!

## 📧 联系方式

如有问题,请查看相关文档或创建Issue。

---

**测试通过率:** 10/10 (100%)
**系统状态:** 生产就绪
**部署方式:** 单机/集群
**安全等级:** 企业级
