#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
存储管理模块 - 管理用户数据、邮件、附件的存储
实现逻辑隔离：不同域名的数据存储在不同目录
"""

import os
import json
import sqlite3
import hashlib
import pickle
import logging
import uuid
import shutil
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import threading

from .protocols import Mail, MailAddress, MailStatus


class StorageManager:
    """存储管理器 - 实现逻辑隔离的数据存储"""
    
    def __init__(self, base_data_path: str):
        """
        初始化存储管理器
        
        Args:
            base_data_path: 基础数据路径，不同域名会创建子目录
        """
        self.base_data_path = Path(base_data_path)
        self.base_data_path.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger("StorageManager")
        self._init_databases()
        
        # 存储锁，确保线程安全
        self.user_lock = threading.RLock()
        self.mail_lock = threading.RLock()
        self.attachment_lock = threading.RLock()
    
    def _init_databases(self):
        """初始化数据库"""
        # 创建主数据库（用于元数据管理）
        self.main_db_path = self.base_data_path / "mail_system.db"
        self._create_main_database()
    
    def _create_main_database(self):
        """创建主数据库表"""
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                domain TEXT NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                storage_limit_mb INTEGER DEFAULT 1024,
                UNIQUE(username, domain)
            )
        ''')
        
        # 邮件元数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mail_metadata (
                mail_id TEXT PRIMARY KEY,
                sender_username TEXT NOT NULL,
                sender_domain TEXT NOT NULL,
                subject TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                mailbox_type TEXT NOT NULL,  -- inbox, sent, draft, trash
                original_mail_id TEXT,  -- 用于回复/转发
                is_encrypted BOOLEAN DEFAULT 0,
                encryption_info TEXT,
                storage_path TEXT NOT NULL
            )
        ''')
        
        # 邮件收件人关系表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mail_recipients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mail_id TEXT NOT NULL,
                recipient_username TEXT NOT NULL,
                recipient_domain TEXT NOT NULL,
                recipient_type TEXT NOT NULL,  -- to, cc, bcc
                FOREIGN KEY (mail_id) REFERENCES mail_metadata(mail_id),
                UNIQUE(mail_id, recipient_username, recipient_domain, recipient_type)
            )
        ''')
        
        # 附件元数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attachments (
                attachment_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                uploaded_by TEXT NOT NULL,
                domain TEXT NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                storage_path TEXT NOT NULL,
                content_type TEXT
            )
        ''')
        
        # 邮件附件关系表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mail_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mail_id TEXT NOT NULL,
                attachment_id TEXT NOT NULL,
                FOREIGN KEY (mail_id) REFERENCES mail_metadata(mail_id),
                FOREIGN KEY (attachment_id) REFERENCES attachments(attachment_id)
            )
        ''')
        
        # 群组表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                creator_username TEXT NOT NULL,
                creator_domain TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                is_public BOOLEAN DEFAULT 0
            )
        ''')
        
        # 群组成员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                member_username TEXT NOT NULL,
                member_domain TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'member',
                FOREIGN KEY (group_id) REFERENCES groups(group_id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_domain ON users(domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mail_sender ON mail_metadata(sender_username, sender_domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mail_recipients ON mail_recipients(recipient_username, recipient_domain)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mail_timestamp ON mail_metadata(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_mail_mailbox ON mail_metadata(mailbox_type)')
        
        conn.commit()
        conn.close()
    
    # ========== 用户管理 ==========
    
    def user_exists(self, username: str, domain: str) -> bool:
        """检查用户是否存在"""
        with self.user_lock:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT 1 FROM users WHERE username = ? AND domain = ?",
                (username, domain)
            )
            
            exists = cursor.fetchone() is not None
            conn.close()
            
            return exists
    
    def create_user(self, username: str, domain: str, password: str, 
                   email: str, **kwargs) -> Dict[str, Any]:
        """创建新用户"""
        
        with self.user_lock:
            if self.user_exists(username, domain):
                raise ValueError(f"User {username}@{domain} already exists")
            
            # 创建用户数据目录
            user_data_dir = self._get_user_data_dir(username, domain)
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建用户配置文件
            user_config = {
                "username": username,
                "domain": domain,
                "email": email,
                "created_at": datetime.now().isoformat(),
                "storage_used_mb": 0,
                "mailboxes": {
                    "inbox": {"count": 0, "size_mb": 0},
                    "sent": {"count": 0, "size_mb": 0},
                    "draft": {"count": 0, "size_mb": 0},
                    "trash": {"count": 0, "size_mb": 0}
                }
            }
            user_config.update(kwargs)
            
            user_config_path = user_data_dir / "user_config.json"
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, ensure_ascii=False, indent=2)
            
            # 在数据库中插入用户记录
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # 在实际应用中，应该使用安全管理器的哈希密码
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO users 
                (username, domain, email, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                username,
                domain,
                email,
                password_hash,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"User created: {username}@{domain}")
            
            return {
                "username": username,
                "domain": domain,
                "email": email,
                "created_at": user_config["created_at"],
                "data_directory": str(user_data_dir)
            }
    
    def authenticate_user(self, username: str, domain: str, password: str) -> Optional[Dict[str, Any]]:
        """验证用户凭据"""
        
        with self.user_lock:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # 在实际应用中，应该使用安全管理器的密码验证
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            cursor.execute('''
                SELECT username, domain, email, created_at, last_login
                FROM users 
                WHERE username = ? AND domain = ? AND password_hash = ? AND is_active = 1
            ''', (username, domain, password_hash))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                "username": row[0],
                "domain": row[1],
                "email": row[2],
                "created_at": row[3],
                "last_login": row[4]
            }
    
    def update_user_last_login(self, username: str, domain: str):
        """更新用户最后登录时间"""
        
        with self.user_lock:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users 
                SET last_login = ?
                WHERE username = ? AND domain = ?
            ''', (datetime.now().isoformat(), username, domain))
            
            conn.commit()
            conn.close()
    
    def get_user_info(self, username: str, domain: str) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        
        with self.user_lock:
            # 从数据库获取基本信息
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT username, domain, email, created_at, last_login, storage_limit_mb
                FROM users 
                WHERE username = ? AND domain = ? AND is_active = 1
            ''', (username, domain))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # 从配置文件获取详细统计
            user_data_dir = self._get_user_data_dir(username, domain)
            user_config_path = user_data_dir / "user_config.json"
            
            user_info = {
                "username": row[0],
                "domain": row[1],
                "email": row[2],
                "created_at": row[3],
                "last_login": row[4],
                "storage_limit_mb": row[5]
            }
            
            if user_config_path.exists():
                try:
                    with open(user_config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        user_info.update(config_data)
                except Exception as e:
                    self.logger.error(f"Error reading user config: {e}")
            
            return user_info
    
    # ========== 邮件存储 ==========
    
    def save_mail(self, mail: Mail, username: str, domain: str, 
                 mailbox_type: str = "inbox") -> bool:
        """保存邮件到指定邮箱"""
        
        with self.mail_lock:
            try:
                # 获取用户数据目录
                user_data_dir = self._get_user_data_dir(username, domain)
                mail_storage_dir = user_data_dir / "mails" / mailbox_type
                mail_storage_dir.mkdir(parents=True, exist_ok=True)
                
                # 邮件存储路径
                mail_storage_path = mail_storage_dir / f"{mail.mail_id}.json"
                
                # 保存邮件数据
                mail_data = mail.to_dict()
                with open(mail_storage_path, 'w', encoding='utf-8') as f:
                    json.dump(mail_data, f, ensure_ascii=False, indent=2)
                
                # 在数据库中记录邮件元数据
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                # 插入邮件元数据
                cursor.execute('''
                    INSERT OR REPLACE INTO mail_metadata 
                    (mail_id, sender_username, sender_domain, subject, timestamp, 
                     status, mailbox_type, storage_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    mail.mail_id,
                    mail.sender.username,
                    mail.sender.domain,
                    mail.subject,
                    mail.timestamp.isoformat(),
                    mail.status.value,
                    mailbox_type,
                    str(mail_storage_path)
                ))
                
                # 插入收件人关系
                for recipient in mail.recipients:
                    cursor.execute('''
                        INSERT OR IGNORE INTO mail_recipients 
                        (mail_id, recipient_username, recipient_domain, recipient_type)
                        VALUES (?, ?, ?, ?)
                    ''', (mail.mail_id, recipient.username, recipient.domain, 'to'))
                
                # 插入抄送收件人
                if mail.cc_recipients:
                    for recipient in mail.cc_recipients:
                        cursor.execute('''
                            INSERT OR IGNORE INTO mail_recipients 
                            (mail_id, recipient_username, recipient_domain, recipient_type)
                            VALUES (?, ?, ?, ?)
                        ''', (mail.mail_id, recipient.username, recipient.domain, 'cc'))
                
                # 插入密送收件人
                if mail.bcc_recipients:
                    for recipient in mail.bcc_recipients:
                        cursor.execute('''
                            INSERT OR IGNORE INTO mail_recipients 
                            (mail_id, recipient_username, recipient_domain, recipient_type)
                            VALUES (?, ?, ?, ?)
                        ''', (mail.mail_id, recipient.username, recipient.domain, 'bcc'))
                
                # 插入附件关系
                if mail.attachments:
                    for attachment_id in mail.attachments:
                        cursor.execute('''
                            INSERT OR IGNORE INTO mail_attachments 
                            (mail_id, attachment_id)
                            VALUES (?, ?)
                        ''', (mail.mail_id, attachment_id))
                
                conn.commit()
                conn.close()
                
                # 更新用户统计
                self._update_user_mail_statistics(username, domain, mailbox_type)
                
                self.logger.debug(f"Mail saved: {mail.mail_id} to {username}@{domain}/{mailbox_type}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving mail {mail.mail_id}: {e}")
                return False
    
    def get_mail(self, mail_id: str, username: str, domain: str) -> Optional[Mail]:
        """获取邮件"""
        
        with self.mail_lock:
            try:
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                # 获取邮件元数据
                cursor.execute('''
                    SELECT storage_path, mailbox_type
                    FROM mail_metadata 
                    WHERE mail_id = ? AND (
                        sender_username = ? AND sender_domain = ?
                        OR mail_id IN (
                            SELECT mail_id FROM mail_recipients 
                            WHERE recipient_username = ? AND recipient_domain = ?
                        )
                    )
                ''', (mail_id, username, domain, username, domain))
                
                row = cursor.fetchone()
                conn.close()
                
                if not row:
                    return None
                
                storage_path, mailbox_type = row
                
                # 检查存储路径是否属于正确的用户目录
                if not self._is_valid_user_path(storage_path, username, domain):
                    self.logger.warning(f"Invalid mail access attempt: {mail_id} by {username}@{domain}")
                    return None
                
                # 从文件加载邮件数据
                with open(storage_path, 'r', encoding='utf-8') as f:
                    mail_data = json.load(f)
                
                # 转换为Mail对象
                mail = Mail.from_dict(mail_data)
                return mail
                
            except Exception as e:
                self.logger.error(f"Error getting mail {mail_id}: {e}")
                return None
    
    def get_user_mails(self, username: str, domain: str, 
                      mailbox_type: str = "inbox") -> List[Mail]:
        """获取用户指定邮箱的所有邮件"""
        
        with self.mail_lock:
            try:
                mails = []
                
                # 获取用户数据目录
                user_data_dir = self._get_user_data_dir(username, domain)
                mail_storage_dir = user_data_dir / "mails" / mailbox_type
                
                if not mail_storage_dir.exists():
                    return []
                
                # 从数据库获取邮件ID列表
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT mail_id 
                    FROM mail_metadata 
                    WHERE mailbox_type = ? AND (
                        sender_username = ? AND sender_domain = ?
                        OR mail_id IN (
                            SELECT mail_id FROM mail_recipients 
                            WHERE recipient_username = ? AND recipient_domain = ?
                        )
                    )
                    ORDER BY timestamp DESC
                ''', (mailbox_type, username, domain, username, domain))
                
                mail_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                # 加载每个邮件
                for mail_id in mail_ids:
                    mail = self.get_mail(mail_id, username, domain)
                    if mail:
                        mails.append(mail)
                
                return mails
                
            except Exception as e:
                self.logger.error(f"Error getting user mails for {username}@{domain}: {e}")
                return []
    
    def withdraw_mail(self, mail_id: str, username: str, domain: str) -> bool:
        """撤回邮件"""
        
        with self.mail_lock:
            try:
                # 获取邮件
                mail = self.get_mail(mail_id, username, domain)
                if not mail:
                    return False
                
                # 验证撤回权限
                if mail.sender.username != username or mail.sender.domain != domain:
                    return False
                
                # 将邮件状态改为已撤回
                mail.status = MailStatus.WITHDRAWN
                
                # 更新所有收件人的邮件状态
                # 在实际应用中，应该更新所有收件人的邮件副本
                # 这里简化为只更新发送者的副本
                
                # 查找邮件存储路径
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT storage_path FROM mail_metadata WHERE mail_id = ?
                ''', (mail_id,))
                
                storage_path = cursor.fetchone()[0]
                conn.close()
                
                # 更新邮件文件
                if storage_path and os.path.exists(storage_path):
                    with open(storage_path, 'r', encoding='utf-8') as f:
                        mail_data = json.load(f)
                    
                    mail_data['status'] = MailStatus.WITHDRAWN.value
                    
                    with open(storage_path, 'w', encoding='utf-8') as f:
                        json.dump(mail_data, f, ensure_ascii=False, indent=2)
                
                # 更新数据库
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE mail_metadata 
                    SET status = ?
                    WHERE mail_id = ?
                ''', (MailStatus.WITHDRAWN.value, mail_id))
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"Mail withdrawn: {mail_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error withdrawing mail {mail_id}: {e}")
                return False
    
    # ========== 附件存储 ==========
    
    def save_attachment(self, attachment_id: str, file_data: bytes, 
                       metadata: Dict[str, Any]) -> bool:
        """保存附件"""
        
        with self.attachment_lock:
            try:
                # 获取上传者信息
                uploaded_by = metadata.get('uploaded_by', 'unknown')
                domain = metadata.get('domain', 'unknown')
                
                # 创建附件存储目录
                attachment_dir = self.base_data_path / "attachments" / domain
                attachment_dir.mkdir(parents=True, exist_ok=True)
                
                # 保存文件
                file_path = attachment_dir / attachment_id
                with open(file_path, 'wb') as f:
                    f.write(file_data)
                
                # 在数据库中记录附件元数据
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO attachments 
                    (attachment_id, filename, file_hash, file_size, 
                     uploaded_by, domain, storage_path, content_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    attachment_id,
                    metadata['filename'],
                    metadata['file_hash'],
                    metadata['file_size'],
                    uploaded_by,
                    domain,
                    str(file_path),
                    metadata.get('content_type')
                ))
                
                conn.commit()
                conn.close()
                
                self.logger.info(f"Attachment saved: {metadata['filename']} ({len(file_data)} bytes)")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving attachment: {e}")
                return False
    
    def get_attachment(self, attachment_id: str) -> Optional[Tuple[bytes, Dict[str, Any]]]:
        """获取附件"""
        
        with self.attachment_lock:
            try:
                conn = sqlite3.connect(self.main_db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT filename, file_hash, file_size, storage_path, content_type
                    FROM attachments 
                    WHERE attachment_id = ?
                ''', (attachment_id,))
                
                row = cursor.fetchone()
                conn.close()
                
                if not row:
                    return None
                
                filename, file_hash, file_size, storage_path, content_type = row
                
                # 读取文件
                with open(storage_path, 'rb') as f:
                    file_data = f.read()
                
                # 验证文件哈希
                actual_hash = hashlib.sha256(file_data).hexdigest()
                if actual_hash != file_hash:
                    self.logger.error(f"Attachment hash mismatch: {attachment_id}")
                    return None
                
                metadata = {
                    'filename': filename,
                    'file_hash': file_hash,
                    'file_size': file_size,
                    'content_type': content_type
                }
                
                return file_data, metadata
                
            except Exception as e:
                self.logger.error(f"Error getting attachment {attachment_id}: {e}")
                return None
    
    def get_attachment_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """通过哈希查找附件"""
        
        with self.attachment_lock:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT attachment_id, filename, file_size, storage_path
                FROM attachments 
                WHERE file_hash = ?
            ''', (file_hash,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            return {
                'attachment_id': row[0],
                'filename': row[1],
                'file_size': row[2],
                'storage_path': row[3]
            }
    
    # ========== 群组管理 ==========
    
    def create_group(self, group_name: str, creator_username: str, 
                    creator_domain: str, members: List[Dict[str, str]], 
                    description: str = None, is_public: bool = False) -> Optional[str]:
        """创建群组"""
        
        try:
            group_id = str(uuid.uuid4())
            
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # 插入群组
            cursor.execute('''
                INSERT INTO groups 
                (group_id, group_name, creator_username, creator_domain, 
                 description, is_public)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                group_id,
                group_name,
                creator_username,
                creator_domain,
                description,
                is_public
            ))
            
            # 插入成员
            for member in members:
                cursor.execute('''
                    INSERT INTO group_members 
                    (group_id, member_username, member_domain)
                    VALUES (?, ?, ?)
                ''', (
                    group_id,
                    member['username'],
                    member['domain']
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Group created: {group_name} ({group_id})")
            return group_id
            
        except Exception as e:
            self.logger.error(f"Error creating group: {e}")
            return None
    
    def get_group(self, group_id: str) -> Optional[Dict[str, Any]]:
        """获取群组信息"""
        
        try:
            conn = sqlite3.connect(self.main_db_path)
            cursor = conn.cursor()
            
            # 获取群组基本信息
            cursor.execute('''
                SELECT group_name, creator_username, creator_domain, 
                       created_at, description, is_public
                FROM groups 
                WHERE group_id = ?
            ''', (group_id,))
            
            group_row = cursor.fetchone()
            if not group_row:
                conn.close()
                return None
            
            # 获取成员
            cursor.execute('''
                SELECT member_username, member_domain, joined_at, role
                FROM group_members 
                WHERE group_id = ?
            ''', (group_id,))
            
            members = []
            for row in cursor.fetchall():
                members.append({
                    'username': row[0],
                    'domain': row[1],
                    'joined_at': row[2],
                    'role': row[3]
                })
            
            conn.close()
            
            return {
                'group_id': group_id,
                'group_name': group_row[0],
                'creator': {
                    'username': group_row[1],
                    'domain': group_row[2]
                },
                'created_at': group_row[3],
                'description': group_row[4],
                'is_public': bool(group_row[5]),
                'members': members,
                'member_count': len(members)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting group {group_id}: {e}")
            return None
    
    # ========== 统计功能 ==========
    
    def get_storage_usage(self, username: str, domain: str) -> float:
        """获取用户存储使用情况（MB）"""
        
        user_data_dir = self._get_user_data_dir(username, domain)
        if not user_data_dir.exists():
            return 0.0
        
        total_size = 0
        for file_path in user_data_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)  # 转换为MB
    
    def _update_user_mail_statistics(self, username: str, domain: str, mailbox_type: str):
        """更新用户邮件统计"""
        
        user_config_path = self._get_user_data_dir(username, domain) / "user_config.json"
        if not user_config_path.exists():
            return
        
        try:
            with open(user_config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # 获取邮箱邮件数量
            mails = self.get_user_mails(username, domain, mailbox_type)
            
            # 更新统计
            if 'mailboxes' not in user_config:
                user_config['mailboxes'] = {}
            
            user_config['mailboxes'][mailbox_type] = {
                'count': len(mails),
                'size_mb': self._get_mailbox_size(username, domain, mailbox_type)
            }
            
            with open(user_config_path, 'w', encoding='utf-8') as f:
                json.dump(user_config, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating user statistics: {e}")
    
    def _get_mailbox_size(self, username: str, domain: str, mailbox_type: str) -> float:
        """获取邮箱大小（MB）"""
        
        mailbox_dir = self._get_user_data_dir(username, domain) / "mails" / mailbox_type
        if not mailbox_dir.exists():
            return 0.0
        
        total_size = 0
        for file_path in mailbox_dir.glob("*.json"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)
    
    # ========== 辅助方法 ==========
    
    def _get_user_data_dir(self, username: str, domain: str) -> Path:
        """获取用户数据目录"""
        # 使用域名和用户名创建隔离的目录结构
        safe_username = self._sanitize_filename(username)
        safe_domain = self._sanitize_filename(domain)
        
        return self.base_data_path / "users" / safe_domain / safe_username
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击"""
        # 移除危险字符
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '..']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # 限制长度
        max_length = 100
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        return sanitized
    
    def _is_valid_user_path(self, path: str, username: str, domain: str) -> bool:
        """检查路径是否属于指定用户"""
        
        user_data_dir = self._get_user_data_dir(username, domain)
        path_obj = Path(path)
        
        try:
            # 检查路径是否在用户目录下
            return user_data_dir in path_obj.parents
        except:
            return False
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        
        self.logger.info(f"Cleaning up data older than {days} days")
        
        try:
            # 清理临时文件
            temp_dir = self.base_data_path / "temp"
            if temp_dir.exists():
                for item in temp_dir.iterdir():
                    if item.is_file():
                        item.unlink()
            
            # 清理过期的会话文件等
            # 在实际应用中，这里可以添加更多清理逻辑
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    # 测试存储管理器
    import tempfile
    
    print("测试存储管理器...")
    
    # 创建临时数据目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建存储管理器
    storage_manager = StorageManager(temp_dir)
    
    # 测试用户创建
    try:
        user = storage_manager.create_user(
            username="testuser",
            domain="example.com",
            password="testpass",
            email="test@example.com"
        )
        print(f"✓ 用户创建成功: {user['username']}@{user['domain']}")
    except Exception as e:
        print(f"✗ 用户创建失败: {e}")
    
    # 测试用户验证
    user_info = storage_manager.authenticate_user("testuser", "example.com", "testpass")
    if user_info:
        print(f"✓ 用户验证成功: {user_info['username']}@{user_info['domain']}")
    else:
        print("✗ 用户验证失败")
    
    # 测试邮件存储
    from protocols import Mail, MailAddress, MailStatus
    import datetime
    
    test_mail = Mail(
        mail_id="test_mail_123",
        sender=MailAddress(username="testuser", domain="example.com"),
        recipients=[MailAddress(username="recipient", domain="example.com")],
        subject="测试邮件",
        body="这是一封测试邮件",
        timestamp=datetime.datetime.now(),
        status=MailStatus.SENT,
        attachments=[]
    )
    
    success = storage_manager.save_mail(test_mail, "recipient", "example.com", "inbox")
    if success:
        print("✓ 邮件存储成功")
    else:
        print("✗ 邮件存储失败")
    
    # 测试邮件读取
    mail = storage_manager.get_mail("test_mail_123", "recipient", "example.com")
    if mail:
        print(f"✓ 邮件读取成功: {mail.subject}")
    else:
        print("✗ 邮件读取失败")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)
    
    print("测试完成")