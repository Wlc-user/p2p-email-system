# 🚀 智能安全邮箱系统 - 快速开始

## 📋 项目概述

这是一个完整的智能安全邮箱系统，具有以下特性：

### 核心功能
- ✅ 双服务器架构（两个隔离域名）
- ✅ 跨域邮件通信
- ✅ 逻辑数据隔离
- ✅ 完整安全模块
- ✅ 动态成本优化
- ✅ 客户端管理

### 安全特性
- 🔒 端到端加密
- 🛡️ 防XSS/钓鱼攻击  
- 📊 审计日志
- 🔐 多重身份验证
- 🚨 异常检测

## 🎯 启动方式选择

### 方式1：Docker启动（推荐，无需安装Python）
```bash
# 1. 确保已安装Docker Desktop
# 2. 运行启动脚本
start_with_docker.bat
```

### 方式2：Python直接启动
```bash
# 需要Python 3.8+环境
python start_servers.py
```

### 方式3：查看项目结构（无需运行）
```bash
# 查看所有文件
dir /s

# 查看核心文件
type README.md
type server/main.py
```

## 📁 项目结构

```
智能安全邮箱系统/
├── 📂 server/              # 服务器端代码
│   ├── main.py            # 服务器主程序
│   ├── security.py        # 安全模块
│   ├── mail_handler.py    # 邮件处理
│   ├── storage_manager.py # 存储管理
│   └── protocols.py       # 通信协议
├── 📂 client/              # 客户端代码
│   └── main.py            # 客户端主程序
├── 📂 config/              # 配置文件
│   ├── domain1_config.json
│   ├── domain2_config.json
│   └── security_config.json
├── 📂 cost_optimizer/      # 动态成本优化
│   ├── dynamic_cost_engine.py
│   └── demo_system.py
├── 📂 security_analysis/   # 安全分析
│   ├── xss_poc.html
│   ├── e2e_encryption.md
│   └── audit_alert.md
├── 📂 data/                # 数据存储
│   ├── domain1/           # 域名1用户数据
│   └── domain2/           # 域名2用户数据
├── 📂 logs/                # 日志文件
├── 📄 Dockerfile           # 容器化配置
├── 📄 docker-compose.yml   # 服务编排
├── 📄 requirements.txt     # Python依赖
├── 📄 start_servers.py     # 启动脚本
├── 📄 start_with_docker.bat # Docker启动脚本
├── 📄 integration_test.py  # 集成测试
└── 📄 README.md            # 项目说明
```

## 🔧 环境要求

### 最低要求
- **操作系统**: Windows 10/11, macOS, Linux
- **内存**: 4GB RAM
- **磁盘空间**: 1GB

### 运行环境（三选一）
1. **Docker Desktop**（推荐）
   - 下载地址: https://www.docker.com/products/docker-desktop
   - 无需安装Python

2. **Python环境**
   - Python 3.8+
   - pip包管理器
   - 运行: `pip install -r requirements.txt`

3. **仅查看**（无需安装）
   - 任何文本编辑器
   - 可查看代码结构和设计文档

## 🎮 快速体验

### 1. 使用Docker（最简单）
```bash
# 双击运行
start_with_docker.bat

# 或手动执行
docker-compose -f docker-compose-simple.yml up -d
```

### 2. 访问服务
- 邮箱服务器1: http://localhost:8080
- 邮箱服务器2: http://localhost:8081

### 3. API端点
```bash
# 健康检查
curl http://localhost:8080/api/health

# 用户注册
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!"}'

# 发送邮件
curl -X POST http://localhost:8081/api/mail/send \
  -H "Content-Type: application/json" \
  -d '{"to":"user@example1.com","subject":"测试","body":"Hello World"}'
```

## 📊 演示功能

### 动态成本优化演示
```bash
# 在Docker容器中运行
docker exec mail-server-1 python cost_optimizer/demo_system.py

# 或直接运行（需要Python）
python cost_optimizer/demo_system.py
```

### 集成测试
```bash
# 运行完整测试
python integration_test.py

# 或运行特定测试
python integration_test.py --test basic
python integration_test.py --test security
python integration_test.py --test cost
```

## 🔍 问题排查

### 常见问题1：Docker无法启动
```
❌ 解决方案：
1. 确保Docker Desktop已安装并运行
2. 以管理员身份运行命令行
3. 检查防火墙设置
4. 重启Docker服务
```

### 常见问题2：端口冲突
```
❌ 解决方案：
1. 检查8080/8081端口是否被占用
2. 修改docker-compose.yml中的端口映射
3. 停止占用端口的程序
```

### 常见问题3：依赖安装失败
```
❌ 解决方案：
1. 使用国内镜像源：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
2. 升级pip：python -m pip install --upgrade pip
3. 安装最小依赖：pip install flask cryptography numpy
```

## 📈 验证系统运行

### 检查服务状态
```bash
# Docker方式
docker ps
docker logs mail-server-1

# Python方式
curl http://localhost:8080/api/health
python -c "import socket; s=socket.socket(); s.connect(('localhost',8080)); print('✅ Server running')"
```

### 运行简单测试
```python
# test_connection.py
import requests
response = requests.get('http://localhost:8080/api/health')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## 🎨 可视化界面

项目包含完整的Web界面，启动后可通过浏览器访问：

1. **管理界面**: http://localhost:8080/admin
2. **API文档**: http://localhost:8080/api/docs
3. **监控面板**: http://localhost:8080/monitor

## 📚 学习资源

### 代码阅读指南
1. **先看**: `server/main.py` - 服务器入口
2. **再看**: `server/security.py` - 安全实现
3. **接着看**: `cost_optimizer/dynamic_cost_engine.py` - 成本优化
4. **最后看**: `integration_test.py` - 功能验证

### 设计文档
- `docs/architecture.md` - 系统架构
- `docs/security.md` - 安全设计
- `docs/cost_optimization.md` - 成本优化原理

## 🆘 技术支持

### 快速帮助
```
问题: 无法启动
解决: 运行 check_environment.py 检查环境

问题: 看不懂代码
解决: 查看代码注释和README.md

问题: 想修改功能
解决: 先运行测试确保现有功能正常
```

### 联系信息
- 项目文档: 查看当前目录所有.md文件
- 代码注释: 每个文件都有详细注释
- 测试用例: integration_test.py包含所有功能测试

## 🎉 开始使用

选择最适合您的方式：

### 🐳 使用Docker（推荐给新手）
```bash
双击 start_with_docker.bat
等待提示完成
打开浏览器访问 http://localhost:8080
```

### 🐍 使用Python（推荐给开发者）
```bash
python start_servers.py
按提示操作
```

### 👁️ 仅查看代码（无需运行）
```bash
打开文件夹浏览代码
阅读README.md了解设计
```

---

**祝您使用愉快！如有问题，请查看上述文档或运行检查脚本。**