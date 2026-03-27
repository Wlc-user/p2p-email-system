#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
协议定义 - 定义客户端和服务器之间的通信协议
"""

import json
import uuid
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum, IntEnum


class MessageType(IntEnum):
    """消息类型枚举"""
    PING = 1                # 心跳检测
    REGISTER = 2           # 用户注册
    LOGIN = 3              # 用户登录
    LOGOUT = 4             # 用户登出
    SEND_MAIL = 5          # 发送邮件
    GET_MAILBOX = 6        # 获取邮箱内容
    WITHDRAW_MAIL = 7      # 撤回邮件
    SEARCH_MAIL = 8        # 搜索邮件
    QUICK_REPLY = 9        # 快速回复
    GROUP_SEND = 10        # 群发邮件
    FORWARD_MAIL = 11      # 转发邮件（服务器间）
    STATUS = 12            # 状态响应
    ERROR = 13             # 错误响应


class MailStatus(Enum):
    """邮件状态枚举"""
    DRAFT = "draft"        # 草稿
    SENT = "sent"          # 已发送
    DELIVERED = "delivered" # 已投递
    READ = "read"          # 已阅读
    WITHDRAWN = "withdrawn" # 已撤回
    FORWARDED = "forwarded" # 已转发
    ERROR = "error"        # 错误


@dataclass
class MailAddress:
    """邮件地址"""
    
    username: str
    domain: str
    
    @property
    def full_address(self) -> str:
        """获取完整邮件地址"""
        return f"{self.username}@{self.domain}"
    
    @classmethod
    def from_string(cls, address: str) -> 'MailAddress':
        """从字符串创建邮件地址"""
        if "@" not in address:
            raise ValueError(f"Invalid email address: {address}")
        
        username, domain = address.split("@", 1)
        return cls(username=username.strip(), domain=domain.strip())
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "username": self.username,
            "domain": self.domain,
            "full_address": self.full_address
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MailAddress':
        """从字典创建"""
        return cls(
            username=data["username"],
            domain=data["domain"]
        )


@dataclass
class Mail:
    """邮件"""
    
    mail_id: str
    sender: MailAddress
    recipients: List[MailAddress]
    subject: str
    body: str
    timestamp: datetime
    status: MailStatus
    attachments: List[str] = field(default_factory=list)
    cc_recipients: Optional[List[MailAddress]] = None
    bcc_recipients: Optional[List[MailAddress]] = None
    reply_to: Optional[MailAddress] = None
    references: List[str] = field(default_factory=list)  # 邮件链引用
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "mail_id": self.mail_id,
            "sender": self.sender.to_dict(),
            "recipients": [r.to_dict() for r in self.recipients],
            "subject": self.subject,
            "body": self.body,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status.value,
            "attachments": self.attachments.copy()
        }
        
        if self.cc_recipients:
            data["cc_recipients"] = [r.to_dict() for r in self.cc_recipients]
        
        if self.bcc_recipients:
            data["bcc_recipients"] = [r.to_dict() for r in self.bcc_recipients]
        
        if self.reply_to:
            data["reply_to"] = self.reply_to.to_dict()
        
        if self.references:
            data["references"] = self.references.copy()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Mail':
        """从字典创建邮件"""
        
        # 解析时间戳
        timestamp_str = data["timestamp"]
        if isinstance(timestamp_str, str):
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            # 如果已经是datetime对象
            timestamp = timestamp_str
        
        # 解析发件人
        sender = MailAddress.from_dict(data["sender"])
        
        # 解析收件人
        recipients = [MailAddress.from_dict(r) for r in data["recipients"]]
        
        # 解析抄送收件人
        cc_recipients = None
        if "cc_recipients" in data and data["cc_recipients"]:
            cc_recipients = [MailAddress.from_dict(r) for r in data["cc_recipients"]]
        
        # 解析密送收件人
        bcc_recipients = None
        if "bcc_recipients" in data and data["bcc_recipients"]:
            bcc_recipients = [MailAddress.from_dict(r) for r in data["bcc_recipients"]]
        
        # 解析回复地址
        reply_to = None
        if "reply_to" in data and data["reply_to"]:
            reply_to = MailAddress.from_dict(data["reply_to"])
        
        # 解析状态
        status = MailStatus(data["status"])
        
        return cls(
            mail_id=data["mail_id"],
            sender=sender,
            recipients=recipients,
            subject=data["subject"],
            body=data["body"],
            timestamp=timestamp,
            status=status,
            attachments=data.get("attachments", []),
            cc_recipients=cc_recipients,
            bcc_recipients=bcc_recipients,
            reply_to=reply_to,
            references=data.get("references", [])
        )


@dataclass
class Message:
    """通信消息"""
    
    message_type: MessageType
    payload: Dict[str, Any] = field(default_factory=dict)
    token: Optional[str] = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "message_type": self.message_type.value,
            "payload": self.payload.copy(),
            "message_id": self.message_id,
            "timestamp": self.timestamp
        }
        
        if self.token:
            data["token"] = self.token
        
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        return cls(
            message_type=MessageType(data["message_type"]),
            payload=data.get("payload", {}),
            token=data.get("token"),
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=data.get("timestamp", time.time())
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """从JSON字符串创建消息"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create(cls, message_type: MessageType, payload: Dict[str, Any], 
              token: Optional[str] = None) -> 'Message':
        """创建消息"""
        return cls(
            message_type=message_type,
            payload=payload,
            token=token
        )


@dataclass
class UserProfile:
    """用户资料"""
    
    username: str
    domain: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    storage_limit_mb: int = 1024
    storage_used_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "username": self.username,
            "domain": self.domain,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
            "storage_limit_mb": self.storage_limit_mb,
            "storage_used_mb": self.storage_used_mb
        }
        
        if self.display_name:
            data["display_name"] = self.display_name
        
        if self.avatar_url:
            data["avatar_url"] = self.avatar_url
        
        if self.last_login:
            data["last_login"] = self.last_login.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """从字典创建"""
        
        # 解析时间戳
        created_at_str = data["created_at"]
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        else:
            created_at = created_at_str
        
        last_login = None
        if "last_login" in data and data["last_login"]:
            last_login_str = data["last_login"]
            if isinstance(last_login_str, str):
                last_login = datetime.fromisoformat(last_login_str.replace('Z', '+00:00'))
            else:
                last_login = last_login_str
        
        return cls(
            username=data["username"],
            domain=data["domain"],
            email=data["email"],
            display_name=data.get("display_name"),
            avatar_url=data.get("avatar_url"),
            created_at=created_at,
            last_login=last_login,
            is_active=data.get("is_active", True),
            storage_limit_mb=data.get("storage_limit_mb", 1024),
            storage_used_mb=data.get("storage_used_mb", 0.0)
        )


@dataclass
class Attachment:
    """附件"""
    
    attachment_id: str
    filename: str
    file_size: int
    content_type: str
    uploaded_by: str
    domain: str
    upload_time: datetime
    file_hash: str
    description: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = {
            "attachment_id": self.attachment_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "uploaded_by": self.uploaded_by,
            "domain": self.domain,
            "upload_time": self.upload_time.isoformat(),
            "file_hash": self.file_hash
        }
        
        if self.description:
            data["description"] = self.description
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Attachment':
        """从字典创建"""
        
        # 解析上传时间
        upload_time_str = data["upload_time"]
        if isinstance(upload_time_str, str):
            upload_time = datetime.fromisoformat(upload_time_str.replace('Z', '+00:00'))
        else:
            upload_time = upload_time_str
        
        return cls(
            attachment_id=data["attachment_id"],
            filename=data["filename"],
            file_size=data["file_size"],
            content_type=data["content_type"],
            uploaded_by=data["uploaded_by"],
            domain=data["domain"],
            upload_time=upload_time,
            file_hash=data["file_hash"],
            description=data.get("description")
        )


@dataclass
class Group:
    """群组"""
    
    group_id: str
    group_name: str
    creator: MailAddress
    members: List[MailAddress]
    created_at: datetime = field(default_factory=datetime.now)
    description: Optional[str] = None
    is_public: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "creator": self.creator.to_dict(),
            "members": [m.to_dict() for m in self.members],
            "created_at": self.created_at.isoformat(),
            "description": self.description,
            "is_public": self.is_public
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Group':
        """从字典创建"""
        
        # 解析创建时间
        created_at_str = data["created_at"]
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        else:
            created_at = created_at_str
        
        return cls(
            group_id=data["group_id"],
            group_name=data["group_name"],
            creator=MailAddress.from_dict(data["creator"]),
            members=[MailAddress.from_dict(m) for m in data["members"]],
            created_at=created_at,
            description=data.get("description"),
            is_public=data.get("is_public", False)
        )


# ========== 响应消息构建器 ==========

def create_success_response(message_id: Optional[str] = None, 
                          data: Optional[Dict[str, Any]] = None) -> Message:
    """创建成功响应"""
    payload = {"status": "success"}
    if data:
        payload.update(data)
    
    return Message.create(
        MessageType.STATUS,
        payload,
        message_id=message_id
    )


def create_error_response(error_message: str, 
                         error_code: Optional[str] = None,
                         message_id: Optional[str] = None) -> Message:
    """创建错误响应"""
    payload = {"error": error_message}
    if error_code:
        payload["error_code"] = error_code
    
    return Message.create(
        MessageType.ERROR,
        payload,
        message_id=message_id
    )


def create_pong_response(server_name: str, 
                        message_id: Optional[str] = None) -> Message:
    """创建PONG响应"""
    return Message.create(
        MessageType.STATUS,
        {
            "status": "pong",
            "server": server_name,
            "timestamp": time.time()
        },
        message_id=message_id
    )


def create_mail_list_response(mails: List[Mail], 
                            mailbox_type: str,
                            message_id: Optional[str] = None) -> Message:
    """创建邮件列表响应"""
    return Message.create(
        MessageType.STATUS,
        {
            "status": "success",
            "mailbox": mailbox_type,
            "mails": [m.to_dict() for m in mails]
        },
        message_id=message_id
    )


def create_mail_sent_response(mail_id: str, 
                            message_id: Optional[str] = None) -> Message:
    """创建邮件发送成功响应"""
    return Message.create(
        MessageType.STATUS,
        {
            "status": "sent",
            "mail_id": mail_id
        },
        message_id=message_id
    )


def create_login_success_response(token: str, user: Dict[str, Any],
                                message_id: Optional[str] = None) -> Message:
    """创建登录成功响应"""
    return Message.create(
        MessageType.STATUS,
        {
            "status": "success",
            "token": token,
            "user": user
        },
        message_id=message_id
    )


# ========== 协议验证 ==========

def validate_message_format(data: Dict[str, Any]) -> bool:
    """验证消息格式"""
    try:
        # 检查必需字段
        if "message_type" not in data:
            return False
        
        # 验证消息类型
        message_type_value = data["message_type"]
        if not isinstance(message_type_value, int):
            return False
        
        # 检查是否是有效的消息类型
        try:
            MessageType(message_type_value)
        except ValueError:
            return False
        
        # 检查payload字段
        if "payload" not in data:
            return False
        
        if not isinstance(data["payload"], dict):
            return False
        
        return True
        
    except Exception:
        return False


def validate_mail_address(address_str: str) -> bool:
    """验证邮件地址格式"""
    try:
        MailAddress.from_string(address_str)
        return True
    except ValueError:
        return False


def validate_mail_data(mail_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """验证邮件数据"""
    try:
        # 检查必需字段
        required_fields = ["mail_id", "sender", "recipients", "subject", 
                          "body", "timestamp", "status"]
        
        for field in required_fields:
            if field not in mail_data:
                return False, f"Missing required field: {field}"
        
        # 验证发件人
        if not validate_mail_address(mail_data["sender"].get("full_address", "")):
            return False, "Invalid sender address"
        
        # 验证收件人
        if not mail_data["recipients"]:
            return False, "No recipients specified"
        
        for recipient in mail_data["recipients"]:
            if not validate_mail_address(recipient.get("full_address", "")):
                return False, f"Invalid recipient address: {recipient}"
        
        # 验证邮件状态
        try:
            MailStatus(mail_data["status"])
        except ValueError:
            return False, f"Invalid mail status: {mail_data['status']}"
        
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {e}"


if __name__ == "__main__":
    # 测试协议模块
    print("测试协议模块...")
    
    # 测试邮件地址
    try:
        address = MailAddress.from_string("user@example.com")
        print(f"✓ 邮件地址解析成功: {address.full_address}")
        
        address_dict = address.to_dict()
        address2 = MailAddress.from_dict(address_dict)
        print(f"✓ 邮件地址序列化/反序列化成功: {address2.full_address}")
        
    except Exception as e:
        print(f"✗ 邮件地址测试失败: {e}")
    
    # 测试消息创建
    try:
        message = Message.create(
            MessageType.LOGIN,
            {"username": "testuser", "password": "testpass"}
        )
        
        json_str = message.to_json()
        message2 = Message.from_json(json_str)
        
        print(f"✓ 消息创建和序列化成功: {message2.message_type.name}")
        
    except Exception as e:
        print(f"✗ 消息测试失败: {e}")
    
    # 测试邮件创建
    try:
        mail = Mail(
            mail_id="test_mail_123",
            sender=MailAddress(username="sender", domain="example.com"),
            recipients=[MailAddress(username="recipient", domain="example.com")],
            subject="测试邮件",
            body="测试内容",
            timestamp=datetime.now(),
            status=MailStatus.SENT
        )
        
        mail_dict = mail.to_dict()
        mail2 = Mail.from_dict(mail_dict)
        
        print(f"✓ 邮件创建和序列化成功: {mail2.subject}")
        
    except Exception as e:
        print(f"✗ 邮件测试失败: {e}")
    
    print("协议模块测试完成")