#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端主程序 - 智能安全邮箱客户端
"""

import sys
import os
import json
import socket
import threading
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from server.protocols import Message, MessageType, Mail, MailAddress, MailStatus
from client.client_ui import ClientUI


class MailClient:
    """邮件客户端"""
    
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 8080):
        """
        初始化邮件客户端
        
        Args:
            server_host: 服务器主机地址
            server_port: 服务器端口
        """
        self.server_host = server_host
        self.server_port = server_port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.auth_token: Optional[str] = None
        self.current_user: Optional[Dict[str, Any]] = None
        self.current_domain: Optional[str] = None
        
        # 客户端配置
        self.config_dir = Path.home() / ".smart_mail_client"
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "client_config.json"
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化UI
        self.ui = ClientUI(self)
        
    def _load_config(self) -> Dict[str, Any]:
        """加载客户端配置"""
        default_config = {
            "servers": {
                "example1.com": {"host": "127.0.0.1", "port": 8080},
                "example2.com": {"host": "127.0.0.1", "port": 8081}
            },
            "recent_users": [],
            "auto_connect": False,
            "save_password": False,
            "theme": "light",
            "language": "zh"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def _save_config(self):
        """保存客户端配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def connect_to_server(self, domain: str) -> bool:
        """连接到指定域名的服务器"""
        try:
            if domain not in self.config['servers']:
                print(f"Unknown domain: {domain}")
                return False
            
            server_info = self.config['servers'][domain]
            
            # 创建socket连接
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # 10秒超时
            
            self.socket.connect((server_info['host'], server_info['port']))
            self.connected = True
            self.current_domain = domain
            
            print(f"Connected to {domain} server")
            return True
            
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开服务器连接"""
        if self.socket:
            try:
                if self.auth_token:
                    self._send_message(Message.create(MessageType.LOGOUT, {}))
                
                self.socket.close()
            except:
                pass
        
        self.socket = None
        self.connected = False
        self.auth_token = None
        self.current_user = None
        print("Disconnected from server")
    
    def _send_message(self, message: Message) -> Optional[Message]:
        """发送消息到服务器并接收响应"""
        if not self.connected or not self.socket:
            print("Not connected to server")
            return None
        
        try:
            # 设置消息的token
            if self.auth_token:
                message.token = self.auth_token
            
            # 发送消息
            message_data = message.to_json().encode('utf-8')
            self.socket.send(message_data)
            
            # 接收响应
            response_data = self.socket.recv(8192)
            if not response_data:
                print("No response from server")
                return None
            
            # 解析响应
            response = Message.from_json(response_data.decode('utf-8'))
            return response
            
        except Exception as e:
            print(f"Error sending/receiving message: {e}")
            return None
    
    def register_user(self, username: str, password: str, email: str) -> bool:
        """注册新用户"""
        if not self.connected:
            print("Not connected to server")
            return False
        
        # 验证输入
        if not username or not password or not email:
            print("Missing required fields")
            return False
        
        # 发送注册请求
        message = Message.create(
            MessageType.REGISTER,
            {
                "username": username,
                "password": password,
                "email": email
            }
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return False
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Registration failed: {error_msg}")
            return False
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'success':
                print(f"User {username} registered successfully")
                
                # 保存到最近用户列表
                user_info = {
                    "username": username,
                    "domain": self.current_domain,
                    "email": email,
                    "last_login": datetime.now().isoformat()
                }
                
                # 添加到最近用户列表
                recent_users = self.config.get('recent_users', [])
                recent_users = [u for u in recent_users if not (
                    u['username'] == username and u['domain'] == self.current_domain
                )]
                recent_users.insert(0, user_info)
                recent_users = recent_users[:10]  # 保留最近10个用户
                
                self.config['recent_users'] = recent_users
                self._save_config()
                
                return True
        
        print("Registration failed")
        return False
    
    def login(self, username: str, password: str, remember_me: bool = False) -> bool:
        """用户登录"""
        if not self.connected:
            print("Not connected to server")
            return False
        
        # 发送登录请求
        message = Message.create(
            MessageType.LOGIN,
            {
                "username": username,
                "password": password,
                "client_ip": "127.0.0.1"  # 在实际应用中应该获取真实IP
            }
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return False
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Login failed: {error_msg}")
            return False
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'success':
                self.auth_token = response.payload.get('token')
                self.current_user = response.payload.get('user')
                
                print(f"User {username} logged in successfully")
                
                # 保存到最近用户列表
                if self.current_user:
                    user_info = {
                        "username": username,
                        "domain": self.current_domain,
                        "email": self.current_user.get('email'),
                        "last_login": datetime.now().isoformat()
                    }
                    
                    recent_users = self.config.get('recent_users', [])
                    recent_users = [u for u in recent_users if not (
                        u['username'] == username and u['domain'] == self.current_domain
                    )]
                    recent_users.insert(0, user_info)
                    recent_users = recent_users[:10]
                    
                    self.config['recent_users'] = recent_users
                    self._save_config()
                
                # 保存密码（如果选择记住我）
                if remember_me and self.config.get('save_password', False):
                    # 注意：在实际应用中应该使用安全的密码管理器
                    pass
                
                return True
        
        print("Login failed")
        return False
    
    def logout(self):
        """用户登出"""
        if self.auth_token:
            message = Message.create(MessageType.LOGOUT, {})
            self._send_message(message)
        
        self.auth_token = None
        self.current_user = None
        print("Logged out")
    
    def send_mail(self, to_addresses: List[str], subject: str, body: str, 
                  attachments: List[str] = None, cc_addresses: List[str] = None,
                  bcc_addresses: List[str] = None) -> Optional[str]:
        """发送邮件"""
        if not self.auth_token or not self.current_user:
            print("Not logged in")
            return None
        
        # 解析收件人地址
        recipients = []
        for address in to_addresses:
            try:
                mail_address = MailAddress.from_string(address)
                recipients.append(mail_address)
            except ValueError as e:
                print(f"Invalid email address {address}: {e}")
                return None
        
        # 解析抄送地址
        cc_recipients = []
        if cc_addresses:
            for address in cc_addresses:
                try:
                    mail_address = MailAddress.from_string(address)
                    cc_recipients.append(mail_address)
                except ValueError as e:
                    print(f"Invalid CC address {address}: {e}")
        
        # 解析密送地址
        bcc_recipients = []
        if bcc_addresses:
            for address in bcc_addresses:
                try:
                    mail_address = MailAddress.from_string(address)
                    bcc_recipients.append(mail_address)
                except ValueError as e:
                    print(f"Invalid BCC address {address}: {e}")
        
        # 创建发送者地址
        sender = MailAddress(
            username=self.current_user['username'],
            domain=self.current_domain
        )
        
        # 创建邮件对象
        mail = Mail(
            mail_id=str(uuid.uuid4()),
            sender=sender,
            recipients=recipients,
            subject=subject,
            body=body,
            timestamp=datetime.now(),
            status=MailStatus.SENT,
            attachments=[],  # 附件处理需要单独实现
            cc_recipients=cc_recipients if cc_recipients else None,
            bcc_recipients=bcc_recipients if bcc_recipients else None
        )
        
        # 发送邮件
        message = Message.create(
            MessageType.SEND_MAIL,
            {"mail": mail.to_dict()}
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return None
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Failed to send mail: {error_msg}")
            return None
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'sent':
                mail_id = response.payload.get('mail_id')
                print(f"Mail sent successfully: {mail_id}")
                return mail_id
        
        print("Failed to send mail")
        return None
    
    def get_mailbox(self, mailbox_type: str = "inbox") -> List[Dict[str, Any]]:
        """获取邮箱内容"""
        if not self.auth_token:
            print("Not logged in")
            return []
        
        message = Message.create(
            MessageType.GET_MAILBOX,
            {"mailbox": mailbox_type}
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return []
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Failed to get mailbox: {error_msg}")
            return []
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'success':
                mails = response.payload.get('mails', [])
                print(f"Retrieved {len(mails)} mails from {mailbox_type}")
                return mails
        
        print("Failed to get mailbox")
        return []
    
    def withdraw_mail(self, mail_id: str) -> bool:
        """撤回邮件"""
        if not self.auth_token:
            print("Not logged in")
            return False
        
        message = Message.create(
            MessageType.WITHDRAW_MAIL,
            {"mail_id": mail_id}
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return False
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Failed to withdraw mail: {error_msg}")
            return False
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'withdrawn':
                print(f"Mail {mail_id} withdrawn successfully")
                return True
        
        print("Failed to withdraw mail")
        return False
    
    def search_mails(self, query: str) -> List[Dict[str, Any]]:
        """搜索邮件"""
        if not self.auth_token:
            print("Not logged in")
            return []
        
        message = Message.create(
            MessageType.SEARCH_MAIL,
            {"query": query}
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return []
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Failed to search mails: {error_msg}")
            return []
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'success':
                results = response.payload.get('results', [])
                print(f"Found {len(results)} results for query: {query}")
                return results
        
        print("Failed to search mails")
        return []
    
    def quick_reply(self, original_mail_id: str, reply_text: str) -> Optional[str]:
        """快速回复邮件"""
        if not self.auth_token:
            print("Not logged in")
            return None
        
        message = Message.create(
            MessageType.QUICK_REPLY,
            {
                "original_mail_id": original_mail_id,
                "reply_text": reply_text
            }
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return None
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Failed to generate quick reply: {error_msg}")
            return None
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'success':
                reply_mail = response.payload.get('reply_mail')
                if reply_mail:
                    # 发送快速回复
                    return self.send_mail(
                        to_addresses=[reply_mail['sender']['full_address']],
                        subject=reply_mail['subject'],
                        body=reply_mail['body']
                    )
        
        print("Failed to generate quick reply")
        return None
    
    def create_group(self, group_name: str, member_addresses: List[str], 
                    description: str = None, is_public: bool = False) -> Optional[str]:
        """创建群组"""
        if not self.auth_token:
            print("Not logged in")
            return None
        
        # 解析成员地址
        members = []
        for address in member_addresses:
            try:
                mail_address = MailAddress.from_string(address)
                members.append(mail_address)
            except ValueError as e:
                print(f"Invalid member address {address}: {e}")
        
        if not members:
            print("No valid member addresses")
            return None
        
        # 创建发送者地址（群组创建者）
        creator = MailAddress(
            username=self.current_user['username'],
            domain=self.current_domain
        )
        
        # 创建群组对象
        group = {
            "group_id": str(uuid.uuid4()),
            "name": group_name,
            "creator": {
                "username": creator.username,
                "domain": creator.domain
            },
            "members": [
                {"username": m.username, "domain": m.domain}
                for m in members
            ],
            "created_at": datetime.now().isoformat(),
            "description": description,
            "is_public": is_public
        }
        
        # TODO: 实现群组创建消息类型
        print(f"Group created: {group_name} with {len(members)} members")
        return group["group_id"]
    
    def group_send(self, group_id: str, subject: str, body: str) -> Optional[str]:
        """群发邮件"""
        if not self.auth_token:
            print("Not logged in")
            return None
        
        # 获取群组信息
        # TODO: 实现群组获取
        
        # 创建邮件
        message = Message.create(
            MessageType.GROUP_SEND,
            {
                "group_id": group_id,
                "mail": {
                    "subject": subject,
                    "body": body,
                    # 其他邮件字段...
                }
            }
        )
        
        response = self._send_message(message)
        
        if not response:
            print("No response from server")
            return None
        
        if response.message_type == MessageType.ERROR:
            error_msg = response.payload.get('error', 'Unknown error')
            print(f"Failed to send group mail: {error_msg}")
            return None
        
        if response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            if status == 'sent':
                mail_id = response.payload.get('mail_id')
                recipient_count = response.payload.get('recipient_count', 0)
                print(f"Group mail sent to {recipient_count} recipients: {mail_id}")
                return mail_id
        
        print("Failed to send group mail")
        return None
    
    def ping_server(self) -> bool:
        """ping服务器检查连接状态"""
        message = Message.create(MessageType.PING, {})
        response = self._send_message(message)
        
        if response and response.message_type == MessageType.STATUS:
            status = response.payload.get('status')
            return status == 'pong'
        
        return False
    
    def run(self):
        """运行客户端"""
        self.ui.run()


def main():
    """主函数"""
    print("=" * 60)
    print("智能安全邮箱客户端")
    print("=" * 60)
    
    # 创建客户端
    client = MailClient()
    
    # 运行客户端
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n客户端已退出")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()