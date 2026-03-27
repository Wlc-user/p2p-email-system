#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全模块 - 实现各种安全功能
"""

import os
import json
import hashlib
import hmac
import time
import random
import string
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class SecurityManager:
    """安全管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化安全管理器
        
        Args:
            config: 安全配置
        """
        self.config = config
        self.logger = logging.getLogger("SecurityManager")
        
        # 初始化密钥
        self._init_keys()
        
        # 初始化登录失败记录
        self.failed_logins: Dict[str, List[float]] = {}
        self.login_lockouts: Dict[str, float] = {}
        
        # 初始化发送限制
        self.send_limits: Dict[str, Dict[str, Any]] = {}
        
        # 初始化会话令牌
        self.active_tokens: Dict[str, Dict[str, Any]] = {}
        
        # 初始化审计数据库
        self._init_audit_db()
        
    def _init_keys(self):
        """初始化加密密钥"""
        # 从配置加载或生成密钥
        self.encryption_key = self.config.get('encryption_key', '').encode('utf-8')
        if len(self.encryption_key) < 32:
            # 如果密钥太短，使用哈希扩展
            self.encryption_key = hashlib.sha256(self.encryption_key).digest()
        
        self.jwt_secret = self.config.get('jwt_secret', '').encode('utf-8')
        if len(self.jwt_secret) < 32:
            self.jwt_secret = hashlib.sha256(self.jwt_secret).digest()
        
        # 盐长度
        self.salt_length = self.config.get('salt_length', 32)
    
    def _init_audit_db(self):
        """初始化审计数据库"""
        audit_db_path = self.config.get('audit_db_path', 'audit_logs/security_audit.db')
        audit_dir = Path(audit_db_path).parent
        audit_dir.mkdir(exist_ok=True)
        
        self.audit_conn = sqlite3.connect(audit_db_path)
        self.audit_cursor = self.audit_conn.cursor()
        
        # 创建审计日志表
        self.audit_cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                username TEXT,
                ip_address TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        self.audit_cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON security_events(timestamp)')
        self.audit_cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON security_events(event_type)')
        self.audit_cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON security_events(username)')
        
        self.audit_conn.commit()
    
    # ========== 密码安全 ==========
    
    def hash_password(self, password: str) -> str:
        """哈希密码"""
        # 生成随机盐
        salt = os.urandom(self.salt_length)
        
        # 使用PBKDF2进行密钥派生
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        # 派生密钥
        key = kdf.derive(password.encode('utf-8'))
        
        # 返回 salt:key 格式
        return f"{salt.hex()}:{key.hex()}"
    
    def verify_password(self, password: str, stored_hash: str) -> bool:
        """验证密码"""
        try:
            # 解析存储的哈希
            salt_hex, key_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            stored_key = bytes.fromhex(key_hex)
            
            # 使用相同的参数验证
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            
            # 验证密码
            kdf.verify(password.encode('utf-8'), stored_key)
            return True
            
        except Exception as e:
            self.logger.warning(f"Password verification failed: {e}")
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        errors = []
        
        # 最小长度
        if len(password) < 8:
            errors.append("密码至少需要8个字符")
        
        # 检查字符类型
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not has_lower:
            errors.append("密码必须包含小写字母")
        if not has_upper:
            errors.append("密码必须包含大写字母")
        if not has_digit:
            errors.append("密码必须包含数字")
        if not has_special:
            errors.append("密码必须包含特殊字符")
        
        # 检查常见弱密码
        weak_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
        if password.lower() in weak_passwords:
            errors.append("密码过于简单，请使用更复杂的密码")
        
        if errors:
            return False, " | ".join(errors)
        return True, "密码强度符合要求"
    
    def validate_username(self, username: str) -> bool:
        """验证用户名格式"""
        # 用户名规则：3-20个字符，只允许字母、数字、下划线
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return bool(re.match(pattern, username))
    
    # ========== 登录安全 ==========
    
    def record_login_attempt(self, username: str, client_ip: str, success: bool):
        """记录登录尝试"""
        current_time = time.time()
        
        # 记录失败尝试
        if not success:
            key = f"{username}@{client_ip}"
            
            if key not in self.failed_logins:
                self.failed_logins[key] = []
            
            self.failed_logins[key].append(current_time)
            
            # 清理15分钟前的记录
            cutoff_time = current_time - (15 * 60)  # 15分钟
            self.failed_logins[key] = [
                t for t in self.failed_logins[key] if t > cutoff_time
            ]
            
            self.logger.warning(f"Failed login attempt for {username} from {client_ip}")
            
            # 检查是否需要锁定
            max_attempts = self.config.get('max_login_attempts', 5)
            if len(self.failed_logins[key]) >= max_attempts:
                lockout_minutes = self.config.get('login_lockout_minutes', 15)
                lockout_until = current_time + (lockout_minutes * 60)
                self.login_lockouts[key] = lockout_until
                
                self.logger.warning(
                    f"Account {username} locked for {lockout_minutes} minutes "
                    f"due to {max_attempts} failed attempts"
                )
        
        # 如果登录成功，清除失败记录
        elif success and username in self.failed_logins:
            del self.failed_logins[username]
            if username in self.login_lockouts:
                del self.login_lockouts[username]
    
    def is_login_blocked(self, username: str, client_ip: str) -> bool:
        """检查登录是否被阻止"""
        key = f"{username}@{client_ip}"
        
        # 检查是否在锁定期内
        if key in self.login_lockouts:
            lockout_until = self.login_lockouts[key]
            if time.time() < lockout_until:
                remaining = int(lockout_until - time.time()) // 60
                self.logger.info(f"Login blocked for {username}: {remaining} minutes remaining")
                return True
            else:
                # 锁定过期，清除记录
                del self.login_lockouts[key]
                if key in self.failed_logins:
                    del self.failed_logins[key]
        
        return False
    
    def generate_captcha(self) -> Tuple[str, str]:
        """生成验证码"""
        # 生成4位随机数字验证码
        captcha_code = ''.join(random.choices(string.digits, k=4))
        
        # 生成简单的文本验证码（实际应用中应该生成图片）
        captcha_text = f"验证码: {captcha_code}"
        
        return captcha_code, captcha_text
    
    # ========== 令牌管理 ==========
    
    def generate_token(self, username: str, domain: str) -> str:
        """生成访问令牌"""
        current_time = time.time()
        token_id = hashlib.sha256(
            f"{username}@{domain}::{current_time}::{random.random()}".encode()
        ).hexdigest()
        
        # 令牌数据
        token_data = {
            'token_id': token_id,
            'username': username,
            'domain': domain,
            'created_at': current_time,
            'expires_at': current_time + (self.config.get('token_expiry_hours', 24) * 3600),
            'last_used': current_time
        }
        
        # 存储令牌
        self.active_tokens[token_id] = token_data
        
        # 返回令牌
        return token_id
    
    def verify_token(self, token: str) -> bool:
        """验证令牌"""
        if token not in self.active_tokens:
            return False
        
        token_data = self.active_tokens[token]
        current_time = time.time()
        
        # 检查令牌是否过期
        if current_time > token_data['expires_at']:
            del self.active_tokens[token]
            return False
        
        # 更新最后使用时间
        token_data['last_used'] = current_time
        
        return True
    
    def get_token_data(self, token: str) -> Optional[Dict[str, Any]]:
        """获取令牌数据"""
        if self.verify_token(token):
            return self.active_tokens[token].copy()
        return None
    
    def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        if token in self.active_tokens:
            del self.active_tokens[token]
            return True
        return False
    
    def cleanup_expired_tokens(self):
        """清理过期令牌"""
        current_time = time.time()
        expired_tokens = []
        
        for token_id, token_data in self.active_tokens.items():
            if current_time > token_data['expires_at']:
                expired_tokens.append(token_id)
        
        for token_id in expired_tokens:
            del self.active_tokens[token_id]
        
        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
    
    # ========== 发送限制 ==========
    
    def check_send_limit(self, username: str, domain: str) -> Tuple[bool, str]:
        """检查发送限制"""
        user_key = f"{username}@{domain}"
        current_time = time.time()
        
        # 初始化用户记录
        if user_key not in self.send_limits:
            self.send_limits[user_key] = {
                'daily_count': 0,
                'daily_reset': self._get_next_reset_time(),
                'last_send_time': 0,
                'minute_count': 0,
                'minute_window': 0
            }
        
        user_limit = self.send_limits[user_key]
        
        # 检查每日重置
        if current_time > user_limit['daily_reset']:
            user_limit['daily_count'] = 0
            user_limit['daily_reset'] = self._get_next_reset_time()
        
        # 检查每日限制
        daily_limit = self.config.get('daily_send_limit', 100)
        if user_limit['daily_count'] >= daily_limit:
            reset_time = datetime.fromtimestamp(user_limit['daily_reset']).strftime('%H:%M:%S')
            return False, f"已达到每日发送限制 ({daily_limit}封)，将在 {reset_time} 重置"
        
        # 检查分钟级频率限制
        rate_limit = self.config.get('rate_limit_per_minute', 60)
        minute_window = current_time // 60
        
        if minute_window != user_limit['minute_window']:
            user_limit['minute_window'] = minute_window
            user_limit['minute_count'] = 0
        
        if user_limit['minute_count'] >= rate_limit:
            return False, f"发送频率过高，请稍后再试 (每分钟最多 {rate_limit} 封)"
        
        # 检查最小发送间隔
        min_interval = 2  # 最小2秒间隔
        if current_time - user_limit['last_send_time'] < min_interval:
            return False, f"发送间隔太短，请等待 {min_interval} 秒"
        
        return True, ""
    
    def record_send(self, username: str, domain: str):
        """记录邮件发送"""
        user_key = f"{username}@{domain}"
        
        if user_key not in self.send_limits:
            self.send_limits[user_key] = {
                'daily_count': 0,
                'daily_reset': self._get_next_reset_time(),
                'last_send_time': 0,
                'minute_count': 0,
                'minute_window': 0
            }
        
        user_limit = self.send_limits[user_key]
        current_time = time.time()
        
        # 更新计数
        user_limit['daily_count'] += 1
        user_limit['last_send_time'] = current_time
        
        # 更新分钟计数
        minute_window = current_time // 60
        if minute_window == user_limit['minute_window']:
            user_limit['minute_count'] += 1
        else:
            user_limit['minute_window'] = minute_window
            user_limit['minute_count'] = 1
    
    def _get_next_reset_time(self) -> float:
        """获取下一个重置时间（次日0点）"""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        reset_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0)
        return reset_time.timestamp()
    
    # ========== 钓鱼/垃圾邮件检测 ==========
    
    def check_spam_content(self, subject: str, body: str) -> Tuple[bool, float, List[str]]:
        """检查垃圾邮件内容"""
        score = 0.0
        reasons = []
        
        # 检查钓鱼关键词
        phishing_patterns = self.config.get('phishing_patterns', [])
        for pattern in phishing_patterns:
            if pattern.lower() in subject.lower() or pattern.lower() in body.lower():
                score += 0.3
                reasons.append(f"包含钓鱼关键词: {pattern}")
        
        # 检查垃圾邮件关键词
        spam_keywords = self.config.get('spam_keywords', [])
        for keyword in spam_keywords:
            if keyword in subject or keyword in body:
                score += 0.2
                reasons.append(f"包含垃圾邮件关键词: {keyword}")
        
        # 检查URL数量
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, body)
        if len(urls) > 3:
            score += 0.2 * min(len(urls) - 3, 5)  # 最多加1分
            reasons.append(f"包含过多URL链接: {len(urls)}个")
        
        # 检查大写字母比例
        if subject:
            total_chars = len(subject)
            upper_chars = sum(1 for c in subject if c.isupper())
            if total_chars > 0:
                upper_ratio = upper_chars / total_chars
                if upper_ratio > 0.5:  # 超过50%大写
                    score += 0.3
                    reasons.append(f"主题大写字母比例过高: {upper_ratio:.1%}")
        
        # 检查感叹号数量
        exclamation_count = subject.count('!') + body.count('!')
        if exclamation_count > 3:
            score += 0.1 * min(exclamation_count - 3, 5)
            reasons.append(f"包含过多感叹号: {exclamation_count}个")
        
        is_spam = score >= 0.7  # 阈值0.7
        return is_spam, score, reasons
    
    def check_suspicious_sender(self, sender_address: str) -> bool:
        """检查可疑发件人"""
        # 检查发件人格式
        if "@" not in sender_address:
            return True
        
        # 检查域名是否为常见邮箱服务商
        common_domains = ["gmail.com", "qq.com", "163.com", "126.com", "yahoo.com", "outlook.com"]
        sender_domain = sender_address.split("@")[1]
        
        # 如果发件人域名不在常见列表中，可能是可疑的
        if sender_domain not in common_domains:
            # 检查域名格式
            if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', sender_domain):
                return True
        
        return False
    
    # ========== 数据加密 ==========
    
    def encrypt_data(self, data: str) -> Tuple[bytes, bytes, bytes]:
        """加密数据"""
        # 生成随机IV
        iv = os.urandom(16)
        
        # 创建加密器
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        
        encryptor = cipher.encryptor()
        
        # 加密数据
        ciphertext = encryptor.update(data.encode('utf-8')) + encryptor.finalize()
        
        # 获取认证标签
        auth_tag = encryptor.tag
        
        return iv, ciphertext, auth_tag
    
    def decrypt_data(self, iv: bytes, ciphertext: bytes, auth_tag: bytes) -> Optional[str]:
        """解密数据"""
        try:
            # 创建解密器
            cipher = Cipher(
                algorithms.AES(self.encryption_key),
                modes.GCM(iv, auth_tag),
                backend=default_backend()
            )
            
            decryptor = cipher.decryptor()
            
            # 解密数据
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode('utf-8')
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_for_storage(self, data: Dict[str, Any]) -> str:
        """为存储加密数据"""
        # 转换为JSON
        json_data = json.dumps(data, ensure_ascii=False)
        
        # 加密
        iv, ciphertext, auth_tag = self.encrypt_data(json_data)
        
        # 组合所有部分
        encrypted_data = {
            'iv': iv.hex(),
            'ciphertext': ciphertext.hex(),
            'auth_tag': auth_tag.hex()
        }
        
        return json.dumps(encrypted_data)
    
    def decrypt_from_storage(self, encrypted_str: str) -> Optional[Dict[str, Any]]:
        """从存储解密数据"""
        try:
            encrypted_data = json.loads(encrypted_str)
            
            iv = bytes.fromhex(encrypted_data['iv'])
            ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
            auth_tag = bytes.fromhex(encrypted_data['auth_tag'])
            
            plaintext = self.decrypt_data(iv, ciphertext, auth_tag)
            
            if plaintext:
                return json.loads(plaintext)
            
        except Exception as e:
            self.logger.error(f"Storage decryption failed: {e}")
        
        return None
    
    # ========== 附件安全 ==========
    
    def validate_attachment(self, filename: str, file_size: int) -> Tuple[bool, str]:
        """验证附件安全性"""
        # 检查文件大小
        max_size_mb = self.config.get('max_attachments_mb', 20)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"附件大小超过限制 ({max_size_mb}MB)"
        
        # 检查文件扩展名
        allowed_extensions = self.config.get('allowed_file_types', [])
        if not allowed_extensions:
            return True, ""  # 如果没有限制，允许所有文件类型
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext not in allowed_extensions:
            return False, f"不允许的文件类型: .{file_ext}"
        
        # 检查文件名安全性
        if self._is_malicious_filename(filename):
            return False, "可疑的文件名"
        
        return True, ""
    
    def _is_malicious_filename(self, filename: str) -> bool:
        """检查是否为恶意文件名"""
        # 检查路径遍历攻击
        malicious_patterns = [
            "..", "/", "\\", ":", "*", "?", "\"", "<", ">", "|"
        ]
        
        for pattern in malicious_patterns:
            if pattern in filename:
                return True
        
        # 检查危险扩展名
        dangerous_extensions = [
            "exe", "bat", "cmd", "sh", "js", "vbs", "ps1", "jar"
        ]
        
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        if file_ext in dangerous_extensions:
            return True
        
        return False
    
    def calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            # 逐块读取文件
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    # ========== 邮件撤回验证 ==========
    
    def verify_withdrawal_request(self, mail_id: str, username: str, 
                                 domain: str, request_token: str) -> bool:
        """验证邮件撤回请求"""
        # 生成预期的令牌
        expected_token = self._generate_withdrawal_token(mail_id, username, domain)
        
        # 使用恒定时间比较防止时序攻击
        return hmac.compare_digest(request_token, expected_token)
    
    def _generate_withdrawal_token(self, mail_id: str, username: str, domain: str) -> str:
        """生成邮件撤回令牌"""
        # 使用HMAC生成令牌
        message = f"{mail_id}:{username}:{domain}"
        hmac_obj = hmac.new(self.jwt_secret, message.encode('utf-8'), hashlib.sha256)
        return hmac_obj.hexdigest()
    
    # ========== 审计日志 ==========
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], 
                          severity: str = "INFO", username: str = None, ip_address: str = None):
        """记录安全事件"""
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'details': details
        }
        
        # 记录到日志文件
        log_message = f"[{severity}] {event_type}: {json.dumps(details)}"
        
        if severity == "ERROR":
            self.logger.error(log_message)
        elif severity == "WARNING":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 保存到安全事件数据库
        if self.config.get('audit_log_enabled', True):
            self._save_audit_event(event_data, username, ip_address)
    
    def _save_audit_event(self, event_data: Dict[str, Any], username: str = None, ip_address: str = None):
        """保存审计事件到数据库"""
        try:
            self.audit_cursor.execute('''
                INSERT INTO security_events 
                (timestamp, event_type, severity, username, ip_address, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                event_data['timestamp'],
                event_data['event_type'],
                event_data['severity'],
                username,
                ip_address,
                json.dumps(event_data['details'], ensure_ascii=False)
            ))
            self.audit_conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to save audit event: {e}")
    
    def get_audit_events(self, limit: int = 100, event_type: str = None, 
                        username: str = None, start_date: str = None, 
                        end_date: str = None) -> List[Dict[str, Any]]:
        """获取审计事件"""
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        if username:
            query += " AND username = ?"
            params.append(username)
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        self.audit_cursor.execute(query, params)
        rows = self.audit_cursor.fetchall()
        
        columns = [desc[0] for desc in self.audit_cursor.description]
        events = []
        
        for row in rows:
            event = dict(zip(columns, row))
            if event.get('details'):
                event['details'] = json.loads(event['details'])
            events.append(event)
        
        return events
    
    # ========== 安全扫描 ==========
    
    def scan_for_vulnerabilities(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """扫描数据中的安全漏洞"""
        vulnerabilities = []
        
        # 检查SQL注入
        sql_injection_patterns = [
            r"(\s|^)(select|insert|update|delete|drop|create|alter)\s",
            r"(\s|^)union\s+select",
            r"(\s|^)or\s+1\s*=\s*1",
            r"(\s|^)--"
        ]
        
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in sql_injection_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        vulnerabilities.append({
                            'type': 'SQL_INJECTION',
                            'location': key,
                            'description': f"检测到可能的SQL注入攻击: {value[:50]}...",
                            'severity': 'HIGH'
                        })
                        break
        
        # 检查XSS攻击
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"alert\s*\(",
            r"eval\s*\("
        ]
        
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        vulnerabilities.append({
                            'type': 'XSS',
                            'location': key,
                            'description': f"检测到可能的XSS攻击: {value[:50]}...",
                            'severity': 'HIGH'
                        })
                        break
        
        # 检查命令注入
        cmd_injection_patterns = [
            r";\s*(ls|dir|cat|type|rm|del|mkdir|cp|mv)",
            r"\|\s*(ls|dir|cat|type|rm|del|mkdir|cp|mv)",
            r"(\s|^)(echo|ping|netstat|whoami|id)(\s|$)"
        ]
        
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in cmd_injection_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        vulnerabilities.append({
                            'type': 'COMMAND_INJECTION',
                            'location': key,
                            'description': f"检测到可能的命令注入攻击: {value[:50]}...",
                            'severity': 'CRITICAL'
                        })
                        break
        
        return vulnerabilities
    
    # ========== 资源清理 ==========
    
    def cleanup(self):
        """清理资源"""
        # 清理过期令牌
        self.cleanup_expired_tokens()
        
        # 清理审计数据库连接
        if hasattr(self, 'audit_conn'):
            self.audit_conn.close()
        
        self.logger.info("Security manager cleaned up successfully")

# ========== 辅助函数 ==========

def generate_secure_key(length: int = 32) -> str:
    """生成安全的随机密钥"""
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def generate_secure_password(length: int = 16) -> str:
    """生成安全密码"""
    # 确保密码包含各种字符类型
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # 每种类型至少一个字符
    password = [
        random.choice(lowercase),
        random.choice(uppercase),
        random.choice(digits),
        random.choice(symbols)
    ]
    
    # 填充剩余长度
    all_chars = lowercase + uppercase + digits + symbols
    password.extend(random.choices(all_chars, k=length - 4))
    
    # 随机打乱
    random.shuffle(password)
    
    return ''.join(password)

def sanitize_input(input_str: str) -> str:
    """清理输入字符串，防止注入攻击"""
    if not input_str:
        return ""
    
    # 移除危险字符
    dangerous_chars = ["<", ">", "\"", "'", "\\", "/", "&", ";", "(", ")", "`"]
    sanitized = input_str
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")
    
    # 限制长度
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def validate_email_format(email: str) -> bool:
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def calculate_entropy(password: str) -> float:
    """计算密码熵"""
    if not password:
        return 0.0
    
    # 字符集大小估计
    char_set_size = 0
    
    if any(c.islower() for c in password):
        char_set_size += 26
    if any(c.isupper() for c in password):
        char_set_size += 26
    if any(c.isdigit() for c in password):
        char_set_size += 10
    if any(not c.isalnum() for c in password):
        char_set_size += 32  # 常见特殊字符
    
    # 计算熵
    if char_set_size == 0:
        return 0.0
    
    entropy = len(password) * (math.log(char_set_size) / math.log(2))
    return entropy

def get_client_fingerprint(request_data: Dict[str, Any]) -> str:
    """获取客户端指纹"""
    fingerprint_data = [
        request_data.get('user_agent', ''),
        request_data.get('accept_language', ''),
        request_data.get('platform', ''),
        request_data.get('timezone', ''),
        request_data.get('screen_resolution', '')
    ]
    
    fingerprint_str = '|'.join(str(item) for item in fingerprint_data)
    return hashlib.sha256(fingerprint_str.encode()).hexdigest()

if __name__ == "__main__":
    # 测试安全模块
    import math
    
    # 基本配置
    config = {
        'encryption_key': 'test_encryption_key_1234567890',
        'jwt_secret': 'test_jwt_secret_1234567890',
        'salt_length': 32,
        'max_login_attempts': 5,
        'login_lockout_minutes': 15,
        'daily_send_limit': 100,
        'rate_limit_per_minute': 60,
        'max_attachments_mb': 20,
        'allowed_file_types': ['txt', 'pdf', 'doc', 'docx', 'jpg', 'png', 'zip'],
        'phishing_patterns': ['紧急', '密码', '账户', '验证', '登录'],
        'spam_keywords': ['促销', '优惠', '免费', '获奖', '幸运'],
        'audit_log_enabled': True,
        'audit_db_path': 'test_audit.db'
    }
    
    # 初始化安全管理器
    security_manager = SecurityManager(config)
    
    # 测试密码哈希
    password = "TestPassword123!"
    hashed = security_manager.hash_password(password)
    verified = security_manager.verify_password(password, hashed)
    print(f"密码哈希测试: {verified}")
    
    # 测试密码强度验证
    is_strong, message = security_manager.validate_password_strength(password)
    print(f"密码强度测试: {is_strong} - {message}")
    
    # 测试令牌管理
    token = security_manager.generate_token("testuser", "domain1.com")
    is_valid = security_manager.verify_token(token)
    print(f"令牌验证测试: {is_valid}")
    
    # 测试垃圾邮件检测
    is_spam, score, reasons = security_manager.check_spam_content(
        "紧急！您的账户需要验证！",
        "请立即点击链接验证您的账户：http://example.com/verify"
    )
    print(f"垃圾邮件检测测试: {is_spam} (得分: {score:.2f})")
    
    # 测试生成安全密码
    secure_pass = generate_secure_password()
    print(f"生成的安全密码: {secure_pass}")
    
    # 清理
    security_manager.cleanup()
    print("安全模块测试完成！")