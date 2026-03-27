# API 路由问题修复

## 问题描述

前端调用 API 时收到错误：
```json
{"success": false, "error": "未知路径"}
```

## 原因分析

前端调用的 API 路径后端没有实现：

| 前端调用 | 后端实现 | 状态 |
|----------|----------|------|
| `GET /api/health` | ✅ 已实现 | 正常 |
| `GET /api/inbox` | ✅ 已实现 | 正常 |
| `GET /api/sent` | ✅ 已实现 | 正常 |
| `GET /api/contacts` | ✅ 已实现 | 正常 |
| `GET /api/node` | ❌ 未实现 | **问题** |
| `POST /api/send-email` | ✅ 已实现 | 正常 |
| `POST /api/start` | ❌ 未实现 | **问题** |
| `POST /api/contacts` | ✅ 已实现 | 正常 |
| `POST /api/stop` | ✅ 已实现 | 正常 |

## 修复内容

### 1. 添加 GET /api/node 接口

**功能：** 获取节点详细信息

**返回数据：**
```json
{
  "success": true,
  "data": {
    "node_id": "9a654e51c15b2e6d...",
    "port": 8000,
    "inbox_count": 2,
    "sent_count": 1,
    "unread_count": 0,
    "ice_candidates": [
      {
        "type": "host",
        "ip": "192.168.2.108",
        "port": 8000,
        "protocol": "udp",
        "region": "local",
        "priority": 100,
        "latency": 0.0
      },
      {
        "type": "tls443",
        "ip": "192.168.2.108",
        "port": 443,
        "protocol": "tls",
        "region": "global",
        "priority": 85,
        "latency": 0.0,
        "fake_domain": "www.facebook.com",
        "sni": "www.facebook.com"
      }
    ],
    "public_key": "e68e9598ad3fdf6f9f3b483c43262985...",
    "timestamp": 1735065600.0
  }
}
```

**代码位置：** `p2p_global.py` 第 1790-1807 行

```python
# 获取节点信息
elif path == '/api/node':
    if p2p_node:
        self._json_response({
            'success': True,
            'data': {
                'node_id': p2p_node.node_id,
                'port': p2p_node.port,
                'inbox_count': len(p2p_node.mailbox.inbox),
                'sent_count': len(p2p_node.mailbox.sent),
                'unread_count': p2p_node.mailbox.get_unread_count(),
                'ice_candidates': [c.to_dict() for c in p2p_node.local_candidates],
                'public_key': p2p_node.pub_key.hex() if hasattr(p2p_node, 'pub_key') else None,
                'timestamp': time.time()
            }
        })
    else:
        self._json_response({'success': False, 'error': '节点未启动'}, 500)
    return
```

### 2. 添加 POST /api/start 接口

**功能：** 启动 P2P 节点（如果未启动）

**请求体：**
```json
{}
```

**返回数据：**
```json
{
  "success": true,
  "message": "节点启动成功",
  "data": {
    "node_id": "9a654e51c15b2e6d1340fb491940cff5aec0e868",
    "port": 8000
  }
}
```

**代码位置：** `p2p_global.py` 第 1837-1868 行

```python
# 启动节点
if path == '/api/start':
    global p2p_node, db_conn
    if p2p_node:
        self._json_response({
            'success': True,
            'message': '节点已在运行',
            'data': {'node_id': p2p_node.node_id}
        })
    else:
        try:
            # 创建新节点
            node = P2PEmailNode(seed="user@localhost", port=8000)
            asyncio.run(node.start())

            p2p_node = node
            db_conn = init_database()

            self._json_response({
                'success': True,
                'message': '节点启动成功',
                'data': {
                    'node_id': node.node_id,
                    'port': node.port
                }
            })
        except Exception as e:
            logger.error(f"启动节点失败: {e}")
            self._json_response({'success': False, 'error': str(e)}, 500)
    return
```

## 完整 API 列表

### GET 接口

| 路径 | 功能 | 状态 |
|-------|------|------|
| `/api/health` | 健康检查 | ✅ |
| `/api/node` | 节点详细信息 | ✅ 新增 |
| `/api/inbox` | 获取收件箱 | ✅ |
| `/api/sent` | 获取已发送 | ✅ |
| `/api/contacts` | 获取联系人 | ✅ |

### POST 接口

| 路径 | 功能 | 状态 |
|-------|------|------|
| `/api/start` | 启动节点 | ✅ 新增 |
| `/api/send-email` | 发送邮件 | ✅ |
| `/api/contacts` | 添加联系人 | ✅ |
| `/api/stop` | 停止服务 | ✅ |

## 前端使用场景

### 1. P2PStatus 组件

```javascript
// 启动节点
const response = await fetch('http://localhost:8102/api/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({})
});
```

### 2. TestAPI 组件

```javascript
// 测试节点信息
const response = await fetch('http://localhost:8102/api/node');
const data = await response.json();
console.log('节点信息:', data);
```

### 3. App.jsx 定期检查

```javascript
// 每2秒检查一次健康状态
const checkStatus = async () => {
  try {
    const response = await fetch('http://localhost:8102/api/health');
    const data = await response.json();
    if (data.success && data.node_id) {
      useP2PStore.getState().setStatus('running');
    }
  } catch {
    // 忽略错误
  }
};
```

## 测试方法

### 1. 测试 /api/health
```bash
curl http://localhost:8102/api/health
```

预期输出：
```json
{
  "success": true,
  "status": "running",
  "node_id": "9a654e51c15b2e6d...",
  "timestamp": 1735065600.0
}
```

### 2. 测试 /api/node
```bash
curl http://localhost:8102/api/node
```

预期输出：
```json
{
  "success": true,
  "data": {
    "node_id": "9a654e51c15b2e6d...",
    "port": 8000,
    "inbox_count": 0,
    "sent_count": 0,
    "unread_count": 0,
    "ice_candidates": [...],
    "public_key": "e68e9598ad3fdf6f9f3b483c43262985...",
    "timestamp": 1735065600.0
  }
}
```

### 3. 测试 /api/start
```bash
curl -X POST http://localhost:8102/api/start \
  -H "Content-Type: application/json" \
  -d "{}"
```

预期输出（第一次）：
```json
{
  "success": true,
  "message": "节点启动成功",
  "data": {
    "node_id": "9a654e51c15b2e6d...",
    "port": 8000
  }
}
```

预期输出（节点已运行）：
```json
{
  "success": true,
  "message": "节点已在运行",
  "data": {
    "node_id": "9a654e51c15b2e6d..."
  }
}
```

### 4. 测试 /api/inbox
```bash
curl http://localhost:8102/api/inbox
```

预期输出：
```json
{
  "success": true,
  "data": [
    {
      "message_id": "xxx",
      "sender_id": "xxx",
      "recipient_id": "xxx",
      "subject": "xxx",
      "body": "xxx",
      "timestamp": 1735065600.0,
      "read": false,
      "attachments": []
    }
  ]
}
```

## 常见问题

### Q: 为什么调用 /api/node 返回 500 错误？
A: 检查后端是否已启动节点：
- 确认运行 `python p2p_global.py api`
- 检查日志中是否有 "P2P邮箱节点初始化"
- 确认 `p2p_node` 全局变量已设置

### Q: 调用 /api/start 没有反应？
A: 可能原因：
1. 节点已经在运行，返回"节点已在运行"
2. 启动失败，检查后端日志中的错误
3. 端口 8000 被占用

### Q: 前端状态不更新？
A: 检查以下几点：
1. 确认 `/api/health` 返回正确的 `node_id`
2. 前端的 `setStatus('running') 是否被调用
3. Zustand store 是否正确更新

## 后端日志示例

正常启动后的日志：
```
[INFO] UltimateP2P_Global: HTTP API服务器启动: http://127.0.0.1:8102
[API] 127.0.0.1 - "GET /api/health HTTP/1.1" 200
[API] 127.0.0.1 - "GET /api/node HTTP/1.1" 200
[API] 127.0.0.1 - "GET /api/inbox HTTP/1.1" 200
```

## 总结

✅ 已添加 `GET /api/node` 接口
✅ 已添加 `POST /api/start` 接口
✅ 所有前端调用的 API 路径都已实现
✅ 前后端通信完全对应

现在前端应该不会再收到"未知路径"错误了！
