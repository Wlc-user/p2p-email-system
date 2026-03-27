#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务器管理器 - 管理双域名邮箱服务器
"""

import json
import threading
import logging
import socket
import time
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from dataclasses import asdict

from .protocols import Message, MessageType, Mail, MailAddress, MailStatus
from .mail_handler import MailHandler
from .storage_manager import StorageManager
from .security import SecurityManager


class ServerManager:
    """服务器管理器"""
    
    def __init__(self, config_path: str, domain: str):
        """
        初始化服务器管理器
        
        Args:
            config_path: 配置文件路径
            domain: 服务器域名
        """
        self.domain = domain
        self.config = self._load_config(config_path)
        self.storage_manager = StorageManager(self.config['data_path'])
        self.security_manager = SecurityManager(self.config)
        self.mail_handler = MailHandler(self.storage_manager, self.security_manager)
        
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.client_threads: Dict[str, threading.Thread] = {}
        self.active_sessions: Dict[str, Dict] = {}
        
        self._setup_logging()
        self.logger = logging.getLogger(f"ServerManager.{domain}")
        
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _setup_logging(self):
        """设置日志"""
        log_dir = Path(self.config['data_path']) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'server.log'),
                logging.StreamHandler()
            ]
        )
    
    def start(self):
        """启动服务器"""
        self.logger.info(f"Starting server for domain: {self.domain}")
        
        try:
            # 创建服务器套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.config['server_port']))
            self.server_socket.listen(self.config['max_clients'])
            
            self.running = True
            self.logger.info(f"Server listening on port {self.config['server_port']}")
            
            # 启动监控线程
            monitor_thread = threading.Thread(target=self._monitor_clients, daemon=True)
            monitor_thread.start()
            
            # 启动会话清理线程
            cleanup_thread = threading.Thread(target=self._cleanup_sessions, daemon=True)
            cleanup_thread.start()
            
            # 接受客户端连接
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(f"New connection from {client_address}")
                    
                    # 为每个客户端创建处理线程
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    thread_id = f"{client_address[0]}:{client_address[1]}"
                    self.client_threads[thread_id] = client_thread
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
                    
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise
    
    def stop(self):
        """停止服务器"""
        self.logger.info("Stopping server...")
        self.running = False
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 等待客户端线程结束
        for thread_id, thread in list(self.client_threads.items()):
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("Server stopped")
    
    def _monitor_clients(self):
        """监控客户端连接"""
        while self.running:
            time.sleep(30)  # 每30秒检查一次
            dead_threads = []
            
            for thread_id, thread in self.client_threads.items():
                if not thread.is_alive():
                    dead_threads.append(thread_id)
            
            for thread_id in dead_threads:
                del self.client_threads[thread_id]
                self.logger.debug(f"Removed dead client thread: {thread_id}")
    
    def _cleanup_sessions(self):
        """清理过期的会话"""
        while self.running:
            time.sleep(60)  # 每60秒清理一次
            current_time = time.time()
            expired_sessions = []
            
            for session_id, session_data in self.active_sessions.items():
                if current_time - session_data['last_activity'] > self.config['session_timeout_minutes'] * 60:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
                self.logger.info(f"Cleaned up expired session: {session_id}")
    
    def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """处理客户端连接"""
        client_id = f"{client_address[0]}:{client_address[1]}"
        
        try:
            while self.running:
                # 接收数据
                data = client_socket.recv(8192)
                if not data:
                    break
                
                try:
                    # 解析消息
                    message = Message.from_json(data.decode('utf-8'))
                    self.logger.debug(f"Received message: {message.message_type}")
                    
                    # 处理消息
                    response = self._process_message(message)
                    
                    # 发送响应
                    client_socket.send(response.to_json().encode('utf-8'))
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON from client {client_id}: {e}")
                    error_msg = Message.create(
                        MessageType.ERROR,
                        {"error": "Invalid message format"}
                    )
                    client_socket.send(error_msg.to_json().encode('utf-8'))
                    
                except Exception as e:
                    self.logger.error(f"Error processing message from {client_id}: {e}")
                    error_msg = Message.create(
                        MessageType.ERROR,
                        {"error": f"Internal server error: {str(e)}"}
                    )
                    client_socket.send(error_msg.to_json().encode('utf-8'))
                    
        except Exception as e:
            self.logger.error(f"Client connection error for {client_id}: {e}")
            
        finally:
            client_socket.close()
            if client_id in self.client_threads:
                del self.client_threads[client_id]
            self.logger.info(f"Client disconnected: {client_address}")
    
    def _process_message(self, message: Message) -> Message:
        """处理消息"""
        # 验证令牌（除注册和登录外）
        if message.message_type not in [MessageType.REGISTER, MessageType.LOGIN, MessageType.PING]:
            if not message.token:
                return Message.create(
                    MessageType.ERROR,
                    {"error": "Authentication required"}
                )
            
            # 验证令牌
            if not self.security_manager.verify_token(message.token):
                return Message.create(
                    MessageType.ERROR,
                    {"error": "Invalid or expired token"}
                )
        
        # 更新会话活动时间
        if message.token:
            session_data = self.active_sessions.get(message.token)
            if session_data:
                session_data['last_activity'] = time.time()
        
        # 根据消息类型处理
        try:
            if message.message_type == MessageType.REGISTER:
                return self._handle_register(message)
            elif message.message_type == MessageType.LOGIN:
                return self._handle_login(message)
            elif message.message_type == MessageType.LOGOUT:
                return self._handle_logout(message)
            elif message.message_type == MessageType.SEND_MAIL:
                return self._handle_send_mail(message)
            elif message.message_type == MessageType.GET_MAILBOX:
                return self._handle_get_mailbox(message)
            elif message.message_type == MessageType.WITHDRAW_MAIL:
                return self._handle_withdraw_mail(message)
            elif message.message_type == MessageType.SEARCH_MAIL:
                return self._handle_search_mail(message)
            elif message.message_type == MessageType.QUICK_REPLY:
                return self._handle_quick_reply(message)
            elif message.message_type == MessageType.GROUP_SEND:
                return self._handle_group_send(message)
            elif message.message_type == MessageType.PING:
                return self._handle_ping(message)
            else:
                return Message.create(
                    MessageType.ERROR,
                    {"error": f"Unsupported message type: {message.message_type}"}
                )
                
        except Exception as e:
            self.logger.error(f"Error processing {message.message_type}: {e}")
            return Message.create(
                MessageType.ERROR,
                {"error": f"Processing error: {str(e)}"}
            )
    
    def _handle_register(self, message: Message) -> Message:
        """处理用户注册"""
        payload = message.payload
        username = payload.get('username')
        password = payload.get('password')
        email = payload.get('email')
        
        if not all([username, password, email]):
            return Message.create(
                MessageType.ERROR,
                {"error": "Missing required fields"}
            )
        
        # 验证用户名格式
        if not self.security_manager.validate_username(username):
            return Message.create(
                MessageType.ERROR,
                {"error": "Invalid username format"}
            )
        
        # 验证密码强度
        if not self.security_manager.validate_password(password):
            return Message.create(
                MessageType.ERROR,
                {"error": "Password does not meet security requirements"}
            )
        
        # 检查用户是否已存在
        if self.storage_manager.user_exists(username, self.domain):
            return Message.create(
                MessageType.ERROR,
                {"error": "User already exists"}
            )
        
        # 创建用户
        user_data = self.storage_manager.create_user(
            username=username,
            domain=self.domain,
            password=password,
            email=email
        )
        
        self.logger.info(f"User registered: {username}@{self.domain}")
        
        return Message.create(
            MessageType.STATUS,
            {"status": "success", "user": user_data}
        )
    
    def _handle_login(self, message: Message) -> Message:
        """处理用户登录"""
        payload = message.payload
        username = payload.get('username')
        password = payload.get('password')
        
        if not username or not password:
            return Message.create(
                MessageType.ERROR,
                {"error": "Missing username or password"}
            )
        
        # 检查登录尝试限制
        client_ip = message.payload.get('client_ip', 'unknown')
        if self.security_manager.is_login_blocked(username, client_ip):
            return Message.create(
                MessageType.ERROR,
                {"error": "Too many login attempts. Please try again later."}
            )
        
        # 验证用户凭据
        user_data = self.storage_manager.authenticate_user(
            username=username,
            domain=self.domain,
            password=password
        )
        
        if not user_data:
            # 记录失败的登录尝试
            self.security_manager.record_login_attempt(username, client_ip, False)
            return Message.create(
                MessageType.ERROR,
                {"error": "Invalid username or password"}
            )
        
        # 记录成功的登录
        self.security_manager.record_login_attempt(username, client_ip, True)
        
        # 生成访问令牌
        token = self.security_manager.generate_token(username, self.domain)
        
        # 创建会话
        self.active_sessions[token] = {
            'username': username,
            'domain': self.domain,
            'last_activity': time.time(),
            'client_ip': client_ip
        }
        
        # 更新用户最后登录时间
        self.storage_manager.update_user_last_login(username, self.domain)
        
        self.logger.info(f"User logged in: {username}@{self.domain}")
        
        return Message.create(
            MessageType.STATUS,
            {"status": "success", "token": token, "user": user_data}
        )
    
    def _handle_logout(self, message: Message) -> Message:
        """处理用户登出"""
        token = message.token
        if token in self.active_sessions:
            del self.active_sessions[token]
        
        return Message.create(
            MessageType.STATUS,
            {"status": "logged_out"}
        )
    
    def _handle_send_mail(self, message: Message) -> Message:
        """处理发送邮件"""
        payload = message.payload
        mail_data = payload.get('mail')
        
        if not mail_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "No mail data provided"}
            )
        
        # 获取会话信息
        session_data = self.active_sessions.get(message.token)
        if not session_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "Session not found"}
            )
        
        # 验证发送者权限
        sender_username = session_data['username']
        sender_domain = session_data['domain']
        
        # 创建邮件对象
        mail = Mail.from_dict(mail_data)
        
        # 验证发送者
        if mail.sender.username != sender_username or mail.sender.domain != sender_domain:
            return Message.create(
                MessageType.ERROR,
                {"error": "Sender mismatch"}
            )
        
        # 处理邮件发送
        result = self.mail_handler.send_mail(mail, message.token)
        
        if result['success']:
            return Message.create(
                MessageType.STATUS,
                {"status": "sent", "mail_id": mail.mail_id}
            )
        else:
            return Message.create(
                MessageType.ERROR,
                {"error": result.get('error', 'Failed to send mail')}
            )
    
    def _handle_get_mailbox(self, message: Message) -> Message:
        """处理获取邮箱内容"""
        payload = message.payload
        mailbox_type = payload.get('mailbox', 'inbox')
        
        # 获取会话信息
        session_data = self.active_sessions.get(message.token)
        if not session_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "Session not found"}
            )
        
        username = session_data['username']
        
        # 获取邮件列表
        mails = self.storage_manager.get_user_mails(username, self.domain, mailbox_type)
        
        return Message.create(
            MessageType.STATUS,
            {
                "status": "success",
                "mailbox": mailbox_type,
                "mails": [mail.to_dict() for mail in mails]
            }
        )
    
    def _handle_withdraw_mail(self, message: Message) -> Message:
        """处理撤回邮件"""
        payload = message.payload
        mail_id = payload.get('mail_id')
        
        if not mail_id:
            return Message.create(
                MessageType.ERROR,
                {"error": "No mail ID provided"}
            )
        
        # 获取会话信息
        session_data = self.active_sessions.get(message.token)
        if not session_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "Session not found"}
            )
        
        username = session_data['username']
        
        # 撤回邮件
        success = self.mail_handler.withdraw_mail(mail_id, username, self.domain)
        
        if success:
            return Message.create(
                MessageType.STATUS,
                {"status": "withdrawn", "mail_id": mail_id}
            )
        else:
            return Message.create(
                MessageType.ERROR,
                {"error": "Failed to withdraw mail"}
            )
    
    def _handle_search_mail(self, message: Message) -> Message:
        """处理邮件搜索"""
        payload = message.payload
        query = payload.get('query')
        
        if not query:
            return Message.create(
                MessageType.ERROR,
                {"error": "No search query provided"}
            )
        
        # 获取会话信息
        session_data = self.active_sessions.get(message.token)
        if not session_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "Session not found"}
            )
        
        username = session_data['username']
        
        # 搜索邮件
        results = self.mail_handler.search_mails(query, username, self.domain)
        
        return Message.create(
            MessageType.STATUS,
            {
                "status": "success",
                "results": [mail.to_dict() for mail in results]
            }
        )
    
    def _handle_quick_reply(self, message: Message) -> Message:
        """处理快速回复"""
        payload = message.payload
        original_mail_id = payload.get('original_mail_id')
        reply_text = payload.get('reply_text')
        
        if not original_mail_id or not reply_text:
            return Message.create(
                MessageType.ERROR,
                {"error": "Missing required fields"}
            )
        
        # 获取会话信息
        session_data = self.active_sessions.get(message.token)
        if not session_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "Session not found"}
            )
        
        username = session_data['username']
        
        # 生成快速回复
        reply_mail = self.mail_handler.generate_quick_reply(
            original_mail_id, reply_text, username, self.domain
        )
        
        if reply_mail:
            return Message.create(
                MessageType.STATUS,
                {
                    "status": "success",
                    "reply_mail": reply_mail.to_dict()
                }
            )
        else:
            return Message.create(
                MessageType.ERROR,
                {"error": "Failed to generate quick reply"}
            )
    
    def _handle_group_send(self, message: Message) -> Message:
        """处理群发邮件"""
        payload = message.payload
        mail_data = payload.get('mail')
        group_id = payload.get('group_id')
        
        if not mail_data or not group_id:
            return Message.create(
                MessageType.ERROR,
                {"error": "Missing mail data or group ID"}
            )
        
        # 获取会话信息
        session_data = self.active_sessions.get(message.token)
        if not session_data:
            return Message.create(
                MessageType.ERROR,
                {"error": "Session not found"}
            )
        
        username = session_data['username']
        
        # 验证群组和权限
        group = self.storage_manager.get_group(group_id)
        if not group or group.creator.username != username:
            return Message.create(
                MessageType.ERROR,
                {"error": "Group not found or permission denied"}
            )
        
        # 创建邮件对象
        mail = Mail.from_dict(mail_data)
        
        # 设置收件人为群组成员
        mail.recipients = group.members
        
        # 处理邮件发送
        result = self.mail_handler.send_mail(mail, message.token)
        
        if result['success']:
            return Message.create(
                MessageType.STATUS,
                {"status": "sent", "mail_id": mail.mail_id, "recipient_count": len(group.members)}
            )
        else:
            return Message.create(
                MessageType.ERROR,
                {"error": result.get('error', 'Failed to send mail')}
            )
    
    def _handle_ping(self, message: Message) -> Message:
        """处理心跳检测"""
        return Message.create(
            MessageType.STATUS,
            {"status": "pong", "server": self.domain, "timestamp": time.time()}
        )


if __name__ == "__main__":
    # 测试服务器管理器
    server1 = ServerManager("config/domain1_config.json", "example1.com")
    
    # 在后台启动服务器
    import threading
    server_thread = threading.Thread(target=server1.start, daemon=True)
    server_thread.start()
    
    print("Server started. Press Ctrl+C to stop.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server1.stop()
        print("Server stopped.")