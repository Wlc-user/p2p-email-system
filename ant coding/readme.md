# 智能安全邮箱系统

## 项目概述
一个具有智能功能的双域名安全邮箱系统，包含服务端和客户端，支持邮件管理、安全防护和智能功能。

## 项目结构

```
ant-coding/
├── README.md                  # 项目说明
├── requirements.txt           # Python依赖
├── config/
│   ├── domain1_config.json    # 域名1配置
│   ├── domain2_config.json    # 域名2配置
│   └── security_config.json   # 安全配置
├── server/
│   ├── __init__.py
│   ├── main.py               # 服务器主程序
│   ├── server_manager.py     # 服务器管理器
│   ├── mail_handler.py       # 邮件处理模块
│   ├── storage_manager.py    # 存储管理
│   ├── security.py           # 安全模块
│   ├── intelligence.py       # 智能功能模块
│   └── protocols.py          # 通信协议定义
├── client/
│   ├── __init__.py
│   ├── main.py               # 客户端主程序
│   ├── client_ui.py          # 客户端界面
│   ├── mail_client.py        # 邮件客户端逻辑
│   ├── attachment_handler.py # 附件处理
│   └── security_client.py    # 客户端安全模块
├── data/
│   ├── domain1/              # 域名1数据存储
│   └── domain2/              # 域名2数据存储
├── tests/
│   ├── test_server.py        # 服务器测试
│   ├── test_client.py        # 客户端测试
│   ├── test_security.py      # 安全测试
│   └── test_integration.py   # 集成测试
├── scripts/
│   ├── start_servers.sh      # 启动服务器脚本
│   ├── start_servers.bat     # Windows启动脚本
│   └── test_all.py           # 完整测试脚本
└── docs/
    ├── protocol.md           # 协议说明
    ├── threat_model.md       # 威胁模型
    └── api_docs.md           # API文档
```

## 功能特性

### 核心功能
- 双域名邮箱服务器（domain1.com 和 domain2.com）
- 用户注册/登录系统
- 邮件收发（收件箱、发件箱、草稿箱）
- 邮件撤回功能
- 附件发送与读取

### 智能功能
- 关键词提取与邮件分类
- 邮件搜索（联系人/关键词模糊搜索）
- 快速回复（自动补全上下文）
- 邮件智能分类
- 存储空间优化（附件去重）

### 安全功能
- 登录防爆破（限流、验证码）
- 防滥发/DOS防护
- 敏感信息加密存储
- 钓鱼/垃圾邮件识别
- 通信安全保护

## 快速开始

### 环境要求
- Python 3.8+
- cryptography 库（用于加密）
- sqlite3（内置）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动服务器
```bash
# Linux/Mac
./scripts/start_servers.sh

# Windows
scripts\start_servers.bat
```

### 运行客户端
```bash
python client/main.py
```

## 测试
运行所有测试：
```bash
python scripts/test_all.py
```