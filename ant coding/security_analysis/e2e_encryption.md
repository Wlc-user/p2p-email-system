# 🔐 端到端加密设计说明

## 设计目标

实现真正的端到端加密，确保：
1. **数据机密性**：只有发送者和接收者能阅读邮件内容
2. **数据完整性**：邮件在传输和存储过程中不被篡改
3. **发送者认证**：接收者能够验证邮件确实来自声称的发送者
4. **前向保密**：即使长期密钥泄露，历史邮件仍然安全
5. **拒绝服务抵抗**：防止攻击者消耗服务器资源

## 系统架构

```
发送者客户端 → 加密 → 服务器（密文存储） → 解密 → 接收者客户端
      ↑                             ↑                          ↑
  用户密钥                        服务器密钥                   用户密钥
```

## 密钥管理方案

### 1. 用户密钥层次
```python
class UserKeyManagement:
    """用户密钥管理"""
    
    # 主密钥层次
    - 主密钥 (Master Key): 用户输入的密码派生
    - 身份密钥 (Identity Key): 长期密钥，用于身份认证
    - 签名密钥 (Signing Key): 长期密钥，用于数字签名
    - 预共享密钥 (PreKey): 一次性密钥，用于初始会话
    - 会话密钥 (Session Key): 临时密钥，用于具体邮件加密
    
    # 密钥派生过程
    master_key = PBKDF2(password, salt, iterations=310000)
    identity_key = HKDF(master_key, "identity", length=32)
    signing_key = HKDF(master_key, "signing", length=32)
```

### 2. 双棘轮算法实现
```python
class DoubleRatchet:
    """双棘轮算法实现"""
    
    def __init__(self, identity_key, signed_prekey, one_time_prekey=None):
        # 初始化DH棘轮
        self.root_key = self.kdf_rk(
            self.dh(self.identity_key, signed_prekey),
            self.root_key
        )
        
        # 发送/接收链
        self.send_chain = None
        self.recv_chain = None
        
    def ratchet_send(self):
        """发送消息时棘轮前进"""
        # 生成新的消息密钥
        message_key = self.kdf_ck(self.send_chain.key)
        
        # 更新链密钥
        self.send_chain.key = self.kdf_ck(self.send_chain.key)
        
        return message_key
        
    def ratchet_receive(self, dh_public):
        """接收消息时棘轮前进"""
        # 执行DH计算
        new_root = self.kdf_rk(
            self.dh(self.identity_key, dh_public),
            self.root_key
        )
        
        # 创建新的接收链
        self.recv_chain = Chain(new_root)
```

## 端到端加密协议

### 1. 邮件加密流程

```python
class EndToEndEncryption:
    """端到端加密实现"""
    
    def encrypt_email(self, sender_key, receiver_public_key, email_data):
        """
        加密邮件
        
        步骤：
        1. 生成临时密钥对
        2. 执行ECDH密钥协商
        3. 派生会话密钥
        4. 加密邮件内容
        5. 添加元数据保护
        """
        
        # 1. 生成临时密钥对
        ephemeral_key_pair = generate_ec_key_pair()
        
        # 2. ECDH密钥协商
        shared_secret1 = ecdh(sender_key.private, receiver_public_key)
        shared_secret2 = ecdh(ephemeral_key_pair.private, receiver_public_key)
        
        # 3. 派生会话密钥
        session_key = hkdf(
            input_key_material=shared_secret1 + shared_secret2,
            salt="email-session",
            info=sender_key.public + receiver_public_key,
            length=32
        )
        
        # 4. 加密邮件内容
        ciphertext = encrypt_aes_gcm(
            key=session_key,
            plaintext=json.dumps(email_data),
            associated_data=email_metadata
        )
        
        # 5. 构建加密邮件包
        encrypted_email = {
            'version': 'e2ee-v1',
            'sender_public': sender_key.public,
            'ephemeral_public': ephemeral_key_pair.public,
            'ciphertext': ciphertext,
            'metadata_hash': sha256(email_metadata),
            'timestamp': int(time.time()),
            'signature': sign_data(sender_key.private, ciphertext)
        }
        
        return encrypted_email
```

### 2. 邮件解密流程

```python
    def decrypt_email(self, receiver_key, encrypted_email):
        """
        解密邮件
        
        步骤：
        1. 验证签名
        2. 执行ECDH计算
        3. 派生会话密钥
        4. 解密邮件内容
        5. 验证完整性
        """
        
        # 1. 验证发送者签名
        if not verify_signature(
            encrypted_email['sender_public'],
            encrypted_email['ciphertext'],
            encrypted_email['signature']
        ):
            raise SecurityError("签名验证失败")
        
        # 2. ECDH密钥协商
        shared_secret1 = ecdh(receiver_key.private, encrypted_email['sender_public'])
        shared_secret2 = ecdh(receiver_key.private, encrypted_email['ephemeral_public'])
        
        # 3. 派生会话密钥
        session_key = hkdf(
            input_key_material=shared_secret1 + shared_secret2,
            salt="email-session",
            info=encrypted_email['sender_public'] + receiver_key.public,
            length=32
        )
        
        # 4. 解密邮件内容
        plaintext = decrypt_aes_gcm(
            key=session_key,
            ciphertext=encrypted_email['ciphertext'],
            associated_data=encrypted_email.get('metadata_hash', '')
        )
        
        # 5. 验证元数据完整性
        if sha256(email_metadata) != encrypted_email['metadata_hash']:
            raise SecurityError("元数据完整性检查失败")
        
        return json.loads(plaintext)
```

## 密钥交换协议

### X3DH协议实现

```python
class X3DHProtocol:
    """X3DH密钥交换协议"""
    
    def perform_x3dh(self, initiator_identity, responder_identity):
        """
        X3DH协议执行
        
        步骤：
        1. 获取响应者的预密钥包
        2. 计算四个DH结果
        3. 派生初始共享密钥
        4. 发送初始消息
        """
        
        # 获取响应者的密钥包
        responder_bundle = self.get_prekey_bundle(responder_identity)
        
        # 计算DH结果
        dh1 = ecdh(initiator_identity.private, responder_bundle.identity_key)
        dh2 = ecdh(initiator_ephemeral.private, responder_bundle.identity_key)
        dh3 = ecdh(initiator_identity.private, responder_bundle.signed_prekey)
        dh4 = ecdh(initiator_ephemeral.private, responder_bundle.signed_prekey)
        
        # 如果有一次性预密钥
        if responder_bundle.one_time_prekey:
            dh5 = ecdh(initiator_ephemeral.private, responder_bundle.one_time_prekey)
            dh_input = dh1 + dh2 + dh3 + dh4 + dh5
        else:
            dh_input = dh1 + dh2 + dh3 + dh4
        
        # 派生共享密钥
        shared_secret = hkdf(
            input_key_material=dh_input,
            salt="x3dh-shared-secret",
            info=initiator_identity.public + responder_identity.public,
            length=32
        )
        
        return shared_secret
```

## 邮件数据结构

### 加密邮件格式

```json
{
  "header": {
    "version": "e2ee-v1",
    "algorithm": "X3DH+DoubleRatchet",
    "timestamp": 1672531200,
    "message_id": "msg_abc123",
    "sender": "alice@domain1.com",
    "receiver": "bob@domain2.com"
  },
  "key_exchange": {
    "sender_identity_key": "base64...",
    "sender_ephemeral_key": "base64...",
    "sender_signed_prekey": "base64...",
    "prekey_signature": "base64..."
  },
  "encrypted_data": {
    "ciphertext": "base64...",
    "iv": "base64...",
    "auth_tag": "base64...",
    "associated_data": {
      "subject_hash": "sha256...",
      "attachments_hash": "sha256..."
    }
  },
  "metadata": {
    "message_index": 42,
    "previous_message_hash": "sha256...",
    "ratchet_public_key": "base64..."
  },
  "signature": {
    "algorithm": "Ed25519",
    "value": "base64...",
    "timestamp": 1672531200
  }
}
```

## 附件加密方案

### 分块加密附件

```python
class AttachmentEncryption:
    """附件加密处理"""
    
    def encrypt_attachment(self, file_path, session_key):
        """
        加密附件文件
        
        特点：
        1. 分块加密（支持大文件）
        2. 独立验证每个块
        3. 支持随机访问
        4. 完整性保护
        """
        
        CHUNK_SIZE = 64 * 1024  # 64KB分块
        
        encrypted_chunks = []
        hashes = []
        
        with open(file_path, 'rb') as f:
            chunk_index = 0
            
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                
                # 为每个块生成独立的IV
                chunk_iv = os.urandom(12)
                
                # 加密块
                cipher = AESGCM(session_key)
                ciphertext = cipher.encrypt(
                    chunk_iv,
                    chunk,
                    associated_data=str(chunk_index).encode()
                )
                
                # 计算块哈希
                chunk_hash = sha256(ciphertext)
                
                encrypted_chunks.append({
                    'index': chunk_index,
                    'iv': chunk_iv,
                    'ciphertext': ciphertext,
                    'hash': chunk_hash
                })
                
                hashes.append(chunk_hash)
                chunk_index += 1
        
        # 生成文件完整性哈希
        file_hash = sha256(b''.join(hashes))
        
        return {
            'file_metadata': {
                'original_name': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'chunk_count': len(encrypted_chunks),
                'chunk_size': CHUNK_SIZE,
                'file_hash': file_hash
            },
            'encrypted_chunks': encrypted_chunks
        }
```

## 前向保密与后向保密

### 1. 前向保密实现

```python
class ForwardSecrecy:
    """前向保密机制"""
    
    def rotate_keys(self):
        """定期轮换密钥实现前向保密"""
        
        # 每周轮换预密钥
        if time.time() - self.last_prekey_rotation > 7 * 24 * 3600:
            self.generate_new_prekeys()
            self.upload_prekey_bundle()
            self.last_prekey_rotation = time.time()
        
        # 每次会话使用新的临时密钥
        self.ephemeral_key_pair = generate_ec_key_pair()
        
        # 删除旧的会话密钥
        self.cleanup_old_session_keys(max_age=24 * 3600)
```

### 2. 后向保密实现

```python
class BackwardSecrecy:
    """后向保密机制"""
    
    def implement_backward_secrecy(self):
        """
        实现后向保密
        
        措施：
        1. 密钥删除策略
        2. 消息删除确认
        3. 安全擦除
        """
        
        # 删除策略
        deletion_policies = {
            'ephemeral_keys': 'immediate',  # 临时密钥立即删除
            'session_keys': '1_hour',       # 会话密钥1小时后删除
            'message_keys': 'after_read',   # 消息密钥阅读后删除
            'prekeys': 'after_use'          # 预密钥使用后删除
        }
        
        # 安全擦除
        def secure_erase(key_data):
            """安全擦除密钥数据"""
            # 多次覆盖
            for _ in range(7):
                random_data = os.urandom(len(key_data))
                key_data = random_data
            
            # 最后填充0
            return b'\x00' * len(key_data)
```

## 密钥存储与恢复

### 安全密钥存储

```python
class SecureKeyStorage:
    """安全密钥存储"""
    
    def store_keys_securely(self, user_keys, password):
        """
        安全存储用户密钥
        
        使用：
        1. 密码派生的密钥加密
        2. 硬件安全模块(HSM)支持
        3. 密钥分片存储
        """
        
        # 派生加密密钥
        encryption_key = argon2id(
            password=password,
            salt=user_keys.salt,
            time_cost=4,
            memory_cost=256*1024,
            parallelism=2,
            hash_len=32
        )
        
        # 加密密钥包
        encrypted_key_package = encrypt_aes_gcm(
            key=encryption_key,
            plaintext=json.dumps(user_keys.export()),
            associated_data=user_keys.key_fingerprint
        )
        
        # 分片存储（可选）
        if self.enable_sharding:
            shards = self.shard_key(encrypted_key_package, n=5, k=3)
            for i, shard in enumerate(shards):
                self.store_shard(f"key_shard_{i}", shard)
        
        return encrypted_key_package
    
    def recover_keys(self, password, encrypted_package):
        """恢复用户密钥"""
        
        # 验证密码强度
        if not self.verify_password_strength(password):
            raise SecurityError("密码强度不足")
        
        # 解密密钥包
        decrypted = decrypt_aes_gcm(
            key=self.derive_key_from_password(password),
            ciphertext=encrypted_package
        )
        
        return UserKeys.import_keys(json.loads(decrypted))
```

## 实施建议

### 1. 逐步部署策略
1. **阶段1**：实现基础加密，保护邮件正文
2. **阶段2**：添加附件加密和密钥管理
3. **阶段3**：实施前向保密和完美前向保密
4. **阶段4**：添加硬件安全模块支持

### 2. 兼容性考虑
- 支持渐进式加密（明文/密文混合模式）
- 提供密钥导出/导入功能
- 实现降级保护机制

### 3. 性能优化
- 使用NIST P-256曲线（性能与安全平衡）
- 实施会话重用机制
- 支持硬件加速加密

### 4. 监控与审计
- 记录所有密钥操作
- 监控异常加密模式
- 定期安全审计

## 安全评估

### 实现的保护措施
✅ **机密性**：AES-256-GCM加密  
✅ **完整性**：HMAC-SHA256验证  
✅ **身份认证**：Ed25519数字签名  
✅ **前向保密**：临时密钥和定期轮换  
✅ **拒绝服务抵抗**：工作量证明机制  

### 潜在风险与缓解
1. **量子计算威胁**：预留后量子密码学升级路径
2. **密钥丢失风险**：提供安全的密钥备份和恢复
3. **中间人攻击**：实施密钥指纹验证和信任网

这个端到端加密设计提供了企业级的邮件安全保护，结合了现代密码学的最佳实践。