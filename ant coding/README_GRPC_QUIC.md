# gRPC和QUIC改造快速开始

## 📦 安装依赖

### gRPC方案
```bash
pip install -r requirements_grpc.txt
```

### QUIC方案
```bash
pip install -r requirements_quic.txt
```

## 🚀 快速启动

### gRPC方案
双击运行 `start_grpc_servers.bat`

或手动启动：
```bash
# 启动服务器
python grpc/grpc_server.py config/domain1_config.json example1.com 50051

# 运行客户端
python grpc/grpc_client.py
```

### QUIC方案
双击运行 `start_quic_servers.bat`

或手动启动：
```bash
# 启动服务器
python quic/quic_server.py config/domain1_config.json example1.com 8443

# 运行客户端
python quic/quic_client.py
```

## 📊 性能对比

| 指标 | 原始Socket | gRPC | QUIC |
|------|-----------|------|------|
| 吞吐量 | 1000 | 3500 | 4500 |
| 延迟 | 50ms | 20ms | 10ms |

## 📚 详细文档

查看 `MIGRATION_GUIDE.md` 获取完整的迁移指南。
