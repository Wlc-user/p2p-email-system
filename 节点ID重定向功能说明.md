# 节点ID重定向功能说明

## 功能概述

实现了节点 ID 的便捷交互功能，包括：
1. **STUN 公网地址显示** - 当 STUN 获取到公网地址时自动显示
2. **节点 ID 点击复制** - 点击节点 ID 可复制到剪贴板
3. **联系人快速发信** - 点击联系人节点 ID 可直接跳转到写邮件页面

## 功能详情

### 1. 顶部状态栏 (P2PStatus.jsx)

#### 公网地址显示
- 当 STUN 获取到公网地址后，自动显示公网地址
- 显示格式：`公网: xxx.xxx.xxx.xxx:port`
- 使用地球图标 🌍 标识
- 自动检测并显示（每3秒刷新一次）

#### 节点 ID 复制功能
- 点击节点 ID 区域可复制完整的 40 位节点 ID
- 复制成功后显示绿色对勾 ✅ 图标
- 2秒后自动恢复复制图标

**效果：**
```
┌─────────────────────────────────────────────────────────┐
│ 🟢 已连接    ID: 9a654e51...  🌍 公网: 123.45.67.89:8000  🔒 端到端加密 │
└─────────────────────────────────────────────────────────┘
         ↑ 点击复制         ↑ STUN 成功后显示
```

### 2. 联系人列表 (Contacts.jsx)

#### 节点 ID 复制
- 点击联系人的节点 ID 可复制完整 ID
- 显示绿色对勾反馈
- 鼠标悬停显示复制图标

#### 快速发送邮件
- 点击邮件图标 📧 可直接跳转到写邮件页面
- 自动填入该联系人的节点 ID
- 立即开始写邮件

**效果：**
```
┌─────────────────────────────────────────────────────┐
│ 👤 张三                               📧 🗑️          │
│    707c12e8dd7dc340...  同事                    │
│    ↑ 点击复制节点ID    ↑ 点击发送邮件  ↑ 删除        │
└─────────────────────────────────────────────────────┘
```

### 3. 写邮件页面 (Compose.jsx)

#### 自动填入收件人
- 从联系人列表跳转时，自动填入目标节点 ID
- 无需手动输入或从下拉框选择
- 提高发邮件效率

**流程：**
```
联系人列表 → 点击邮件图标 → 跳转到写邮件页面
                                   ↓
                            自动填入节点 ID
                                   ↓
                            直接填写主题和内容
```

## 技术实现

### P2PStatus.jsx

```javascript
// 公网地址检测
const [publicAddress, setPublicAddress] = useState(null);

useEffect(() => {
  const checkNodeInfo = async () => {
    const response = await fetch('http://localhost:8102/api/node');
    const result = await response.json();
    
    // 检查 ICE candidates 中的公网地址
    const publicCandidate = result.data.ice_candidates?.find(
      c => c.type === 'public' || c.type === 'TLS443'
    );
    
    if (publicCandidate) {
      setPublicAddress(`${publicCandidate.host}:${publicCandidate.port}`);
    }
  };

  checkNodeInfo();
  const interval = setInterval(checkNodeInfo, 3000); // 每3秒检测
  return () => clearInterval(interval);
}, []);
```

### Contacts.jsx

```javascript
// 复制节点 ID
const handleCopyNodeId = (nodeId) => {
  navigator.clipboard.writeText(nodeId);
  setCopiedNodeId(nodeId);
  setTimeout(() => setCopiedNodeId(null), 2000);
};

// 跳转到写邮件页面
const handleSendMessage = (contact) => {
  localStorage.setItem('compose-recipient', contact.node_id);
  navigate('/compose');
};
```

### Compose.jsx

```javascript
// 从 localStorage 读取收件人
useEffect(() => {
  const composeRecipient = localStorage.getItem('compose-recipient');
  if (composeRecipient && !location.state?.to) {
    setTo(composeRecipient);
    localStorage.removeItem('compose-recipient');
  }
}, [location.state]);
```

## 后端 API 要求

### GET /api/node
返回节点信息，包括 ICE candidates：

```json
{
  "success": true,
  "data": {
    "node_id": "9a654e51c15b2e6d...",
    "port": 8000,
    "ice_candidates": [
      {
        "type": "public",
        "host": "123.45.67.89",
        "port": 8000
      },
      {
        "type": "TLS443",
        "host": "123.45.67.89",
        "port": 443
      }
    ]
  }
}
```

## 用户体验优化

1. **视觉反馈**
   - 复制成功显示绿色对勾
   - 鼠标悬停时显示提示和图标
   - 公网地址使用地球图标标识

2. **快捷操作**
   - 一键复制节点 ID
   - 一键发送邮件
   - 自动填充收件人

3. **实时更新**
   - 公网地址自动检测（每3秒）
   - STUN 成功后立即显示

## 使用场景

### 场景1：分享节点 ID
1. 用户在顶部状态栏看到自己的节点 ID
2. 点击节点 ID 区域，自动复制完整 ID
3. 将 ID 发送给其他用户（如通过聊天软件）

### 场景2：添加联系人并发送邮件
1. 用户添加联系人，输入对方的节点 ID
2. 在联系人列表中，点击邮件图标
3. 自动跳转到写邮件页面，收件人已填好
4. 填写主题和内容后发送

### 场景3：检查网络状态
1. 用户查看顶部状态栏
2. 看到公网地址显示，确认 STUN 成功
3. 确认可以与其他节点建立连接

## 注意事项

1. **STUN 成功条件**
   - 需要后端返回有效的 ICE candidates
   - 类型为 `public` 或 `TLS443` 的候选者才显示为公网地址

2. **节点 ID 安全**
   - 节点 ID 是公开信息，可以安全分享
   - 不需要保密

3. **剪贴板权限**
   - 需要浏览器支持 Clipboard API
   - 大多数现代浏览器都支持

## 后续优化建议

1. **节点 ID 分享链接**
   - 生成 `p2pmail://node_id` 协议链接
   - 点击后自动添加为联系人

2. **二维码分享**
   - 将节点 ID 生成二维码
   - 方便手机用户扫描添加

3. **节点状态检测**
   - 检测联系人节点是否在线
   - 显示在线/离线状态
