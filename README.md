<img width="1308" height="822" alt="image" src="https://github.com/user-attachments/assets/0b1b9059-7e71-475b-a59e-479f2e6a895c" /># P2P Global Email System

全球P2P邮箱系统 - 无需中心服务器的端到端加密邮件系统

## 特性

- ✅ **身份层**: 公钥ID系统 (X25519)
- ✅ **发现层**: DHT网络 (节点自动发现)
- ✅ **连接层**: UDP/TCP/TLS443多协议支持
- ✅ **消息层**: 端到端加密邮箱 (ChaCha20-Poly1305)
- ✅ **全球部署**: 全球STUN服务器 + TLS443伪装

## 快速开始

### 1. 安装依赖

```bash
pip install cryptography
```

### 2. 启动系统

```bash
start.bat
```

或直接运行Python:

```bash
python "ant coding/p2p/p2p_global.py" email
```

## 核心文件

- `ant coding/p2p/p2p_global.py` - 核心P2P实现
- `start.bat` - 启动脚本
- `mailbox/` - 邮件存储目录

## 配置

编辑 `p2p_global.py` 中的配置:

```python
ENABLE_STUN = False  # True启用STUN, False仅本地
```

## 使用说明

### 创建邮箱节点

```python
from ant_coding.p2p.p2p_global import P2PEmailNode

# 创建节点
node = P2PEmailNode(seed="user@example.com", port=8000)
await node.start()
```

### 发送邮件

```python
# 交换密钥 (首次)
node.encryption.derive_shared_secret(peer_pub_key, peer_id)

# 发送邮件
await node.send_email(
    recipient_id=peer_id,
    subject="Hello",
    body="Message content"
)
```

### 查看收件箱

```python
node.display_inbox()
node.display_sent()
```

## 架构

### 1. 身份层
- X25519椭圆曲线加密
- 公钥作为唯一身份标识
- 从种子生成确定性身份

### 2. 发现层
- Kademlia DHT网络
- 节点自动发现和路由
- 公钥发布和查询

### 3. 连接层
- UDP打洞 (优先)
- TLS443伪装 (全球可用)
- STUN/TURN NAT穿透
- ICE候选选择

### 4. 消息层
- 端到端加密
- 离线消息存储
- 邮件持久化

## STUN服务器

系统支持全球多个STUN服务器:
- 美国 (East/West)
- 欧洲 (Central/UK)
- 亚洲 (Japan/Singapore)
- 澳大利亚

## TLS443伪装

当常规UDP打洞失败时,系统自动fallback到TLS443:
- 伪装成HTTPS流量
- 使用标准443端口
- SNI域名伪装
- 几乎100%穿透率

## 注意事项

1. 首次运行需要交换公钥
2. STUN需要防火墙开放UDP 3478/19302端口
3. 邮件存储在 `./mailbox/<node_id>/`
4. 建议使用固定端口便于连接

## 故障排查

### STUN连接失败
- 检查防火墙设置
- 尝试设置 `ENABLE_STUN = False`
- 系统会自动fallback到本地模式

### 邮件发送失败
- 确保已交换密钥
- 检查对方节点是否在线
- 查看DHT中是否有对方节点

<img width="1356" height="817" alt="image" src="https://github.com/user-attachments/assets/30ac909d-5536-4f01-a133-1a5498004473" />
<img width="1316" height="767" alt="image" src="https://github.com/user-attachments/assets/9b1ec665-b8d2-473b-9adb-a75df7acba3b" />
<img width="1324" height="800" alt="image" src="https://github.com/user-attachments/assets/6c56ba30-c98a-440a-b5f1-202b290c330b" />
<img width="1308" height="822" alt="image" src="https://github.com/user-attachments/assets/97c77303-539a-4c8e-9cec-8967e31dff6c" />
<img width="1324" height="803" alt="image" src="https://github.com/user-attachments/assets/877a58f2-f3d8-4e5b-b958-aa35b9580cee" />
<img width="1204" height="609" alt="image" src="https://github.com/user-attachments/assets/20dcfcfe-12df-49d3-a185-3c781488b37b" />
<img width="1209" height="617" alt="image" src="https://github.com/user-attachments/assets/2cf65a2f-b5cf-4b07-81ab-dbb45f1e70ad" />

<img width="1118" height="389" alt="image" src="https://github.com/user-attachments/assets/0e61a09d-ca43-4226-af5e-7ba1b1e2255e" />


## 许可

MIT License
