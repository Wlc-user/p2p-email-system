#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件处理模块 - 处理邮件的发送、接收、搜索等功能
"""

import json
import time
import logging
import re
import socket
import threading
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pathlib import Path

from .protocols import Mail, MailAddress, MailStatus, Message, MessageType
from .storage_manager import StorageManager
from .security import SecurityManager


class MailHandler:
    """邮件处理器"""
    
    def __init__(self, storage_manager: StorageManager, security_manager: SecurityManager):
        """
        初始化邮件处理器
        
        Args:
            storage_manager: 存储管理器
            security_manager: 安全管理器
        """
        self.storage_manager = storage_manager
        self.security_manager = security_manager
        self.logger = logging.getLogger("MailHandler")
        
        # 初始化邮件队列和锁
        self.mail_queue = []
        self.queue_lock = threading.Lock()
        
        # 启动邮件发送线程
        self.send_thread = threading.Thread(target=self._mail_sender_worker, daemon=True)
        self.send_thread.start()
        
        # 启动邮件接收线程
        self.receive_thread = threading.Thread(target=self._mail_receiver_worker, daemon=True)
        self.receive_thread.start()
        
        # 服务器间通信配置
        self.inter_domain_servers = {
            "example1.com": {"host": "127.0.0.1", "port": 8080},
            "example2.com": {"host": "127.0.0.1", "port": 8081}
        }
    
    # ========== 邮件发送功能 ==========
    
    def send_mail(self, mail: Mail, token: str) -> Dict[str, Any]:
        """发送邮件"""
        
        try:
            # 验证发送限制
            sender = mail.sender
            can_send, error_msg = self.security_manager.check_send_limit(
                sender.username, sender.domain
            )
            
            if not can_send:
                return {"success": False, "error": error_msg}
            
            # 记录发送
            self.security_manager.record_send(sender.username, sender.domain)
            
            # 检查垃圾邮件
            is_spam, spam_score, spam_reasons = self.security_manager.check_spam_content(
                mail.subject, mail.body
            )
            
            if is_spam:
                self.logger.warning(f"Spam mail detected: {mail.mail_id}, score: {spam_score}")
                # 记录安全事件
                self.security_manager.log_security_event(
                    "SPAM_MAIL_DETECTED",
                    {
                        "mail_id": mail.mail_id,
                        "sender": sender.full_address,
                        "subject": mail.subject,
                        "score": spam_score,
                        "reasons": spam_reasons
                    },
                    severity="WARNING",
                    username=sender.username
                )
            
            # 处理收件人
            all_recipients = mail.recipients.copy()
            if mail.cc_recipients:
                all_recipients.extend(mail.cc_recipients)
            if mail.bcc_recipients:
                all_recipients.extend(mail.bcc_recipients)
            
            # 分组处理收件人（本地 vs 跨域）
            local_recipients = []
            remote_recipients = []
            
            for recipient in all_recipients:
                if recipient.domain == sender.domain:
                    local_recipients.append(recipient)
                else:
                    remote_recipients.append(recipient)
            
            # 保存到发送者发件箱
            self.storage_manager.save_mail(
                mail=mail,
                username=sender.username,
                domain=sender.domain,
                mailbox_type="sent"
            )
            
            # 处理本地收件人
            local_success = []
            local_failed = []
            
            for recipient in local_recipients:
                try:
                    # 保存到收件人收件箱
                    self.storage_manager.save_mail(
                        mail=mail,
                        username=recipient.username,
                        domain=recipient.domain,
                        mailbox_type="inbox"
                    )
                    local_success.append(recipient.full_address)
                    
                except Exception as e:
                    local_failed.append({
                        "address": recipient.full_address,
                        "error": str(e)
                    })
            
            # 处理跨域收件人
            remote_results = []
            if remote_recipients:
                remote_results = self._send_to_other_domains(mail, remote_recipients, token)
            
            # 记录发送结果
            self.logger.info(f"Mail sent: {mail.mail_id}")
            self.logger.info(f"  From: {sender.full_address}")
            self.logger.info(f"  Local recipients: {len(local_success)}成功, {len(local_failed)}失败")
            self.logger.info(f"  Remote recipients: {len(remote_results)}")
            
            return {
                "success": True,
                "mail_id": mail.mail_id,
                "local_success": local_success,
                "local_failed": local_failed,
                "remote_results": remote_results,
                "spam_score": spam_score if is_spam else None
            }
            
        except Exception as e:
            self.logger.error(f"Error sending mail {mail.mail_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _send_to_other_domains(self, mail: Mail, recipients: List[MailAddress], 
                              token: str) -> List[Dict[str, Any]]:
        """发送邮件到其他域"""
        
        results = []
        
        # 按域名分组
        recipients_by_domain = {}
        for recipient in recipients:
            if recipient.domain not in recipients_by_domain:
                recipients_by_domain[recipient.domain] = []
            recipients_by_domain[recipient.domain].append(recipient)
        
        # 发送到每个目标域名
        for target_domain, domain_recipients in recipients_by_domain.items():
            if target_domain not in self.inter_domain_servers:
                # 记录无法投递
                for recipient in domain_recipients:
                    results.append({
                        "address": recipient.full_address,
                        "success": False,
                        "error": f"Unknown domain: {target_domain}"
                    })
                continue
            
            try:
                # 连接到目标服务器
                server_info = self.inter_domain_servers[target_domain]
                
                # 创建转发邮件（移除BCC）
                forward_mail = Mail(
                    mail_id=mail.mail_id,
                    sender=mail.sender,
                    recipients=domain_recipients,
                    subject=mail.subject,
                    body=mail.body,
                    timestamp=mail.timestamp,
                    status=MailStatus.FORWARDED,
                    attachments=mail.attachments,
                    cc_recipients=mail.cc_recipients
                    # 注意：不包含BCC收件人
                )
                
                # 发送到目标服务器
                success = self._forward_to_server(server_info, forward_mail)
                
                for recipient in domain_recipients:
                    if success:
                        results.append({
                            "address": recipient.full_address,
                            "success": True,
                            "domain": target_domain
                        })
                    else:
                        results.append({
                            "address": recipient.full_address,
                            "success": False,
                            "error": f"Failed to forward to domain {target_domain}"
                        })
                
                if success:
                    self.logger.info(f"Mail forwarded to domain {target_domain}: {mail.mail_id}")
                else:
                    self.logger.error(f"Failed to forward mail to domain {target_domain}: {mail.mail_id}")
                    
            except Exception as e:
                self.logger.error(f"Error forwarding to domain {target_domain}: {e}")
                for recipient in domain_recipients:
                    results.append({
                        "address": recipient.full_address,
                        "success": False,
                        "error": str(e)
                    })
        
        return results
    
    def _forward_to_server(self, server_info: Dict[str, Any], mail: Mail) -> bool:
        """转发邮件到服务器"""
        
        try:
            # 创建socket连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            
            sock.connect((server_info["host"], server_info["port"]))
            
            # 创建转发消息
            message = Message.create(
                MessageType.FORWARD_MAIL,  # 假设有转发消息类型
                {"mail": mail.to_dict()}
            )
            
            # 发送消息
            sock.send(message.to_json().encode('utf-8'))
            
            # 接收响应
            response_data = sock.recv(8192)
            response = Message.from_json(response_data.decode('utf-8'))
            
            sock.close()
            
            return response.message_type == MessageType.STATUS and \
                   response.payload.get('status') == 'received'
            
        except Exception as e:
            self.logger.error(f"Error forwarding mail to server: {e}")
            return False
    
    # ========== 邮件接收功能 ==========
    
    def receive_mail(self, mail: Mail, target_domain: str) -> bool:
        """接收外部邮件"""
        
        try:
            # 验证发送者
            if self.security_manager.check_suspicious_sender(mail.sender.full_address):
                self.logger.warning(f"Suspicious sender: {mail.sender.full_address}")
                return False
            
            # 处理每个收件人
            success_count = 0
            for recipient in mail.recipients:
                if recipient.domain == target_domain:
                    try:
                        # 保存到收件箱
                        self.storage_manager.save_mail(
                            mail=mail,
                            username=recipient.username,
                            domain=recipient.domain,
                            mailbox_type="inbox"
                        )
                        success_count += 1
                        
                    except Exception as e:
                        self.logger.error(f"Error saving mail for {recipient.full_address}: {e}")
            
            # 如果有CC收件人
            if mail.cc_recipients:
                for recipient in mail.cc_recipients:
                    if recipient.domain == target_domain:
                        try:
                            # 保存到收件箱
                            self.storage_manager.save_mail(
                                mail=mail,
                                username=recipient.username,
                                domain=recipient.domain,
                                mailbox_type="inbox"
                            )
                            success_count += 1
                            
                        except Exception as e:
                            self.logger.error(f"Error saving CC mail for {recipient.full_address}: {e}")
            
            self.logger.info(f"Received mail {mail.mail_id}: {success_count} recipients processed")
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error receiving mail {mail.mail_id}: {e}")
            return False
    
    # ========== 邮件撤回功能 ==========
    
    def withdraw_mail(self, mail_id: str, username: str, domain: str) -> bool:
        """撤回邮件"""
        
        try:
            # 获取邮件
            mail = self.storage_manager.get_mail(mail_id, username, domain)
            if not mail:
                self.logger.error(f"Mail not found: {mail_id}")
                return False
            
            # 检查撤回权限
            if mail.sender.username != username or mail.sender.domain != domain:
                self.logger.error(f"Permission denied for withdrawing mail: {mail_id}")
                return False
            
            # 检查撤回时间限制（15分钟内）
            time_limit = timedelta(minutes=15)
            mail_age = datetime.now() - mail.timestamp
            
            if mail_age > time_limit:
                self.logger.error(f"Mail too old to withdraw: {mail_age}")
                return False
            
            # 撤回邮件
            success = self.storage_manager.withdraw_mail(mail_id, username, domain)
            
            if success:
                self.logger.info(f"Mail withdrawn: {mail_id}")
                
                # 通知收件人（如果可能）
                self._notify_withdrawal(mail)
                
                # 记录安全事件
                self.security_manager.log_security_event(
                    "MAIL_WITHDRAWN",
                    {
                        "mail_id": mail_id,
                        "sender": mail.sender.full_address,
                        "subject": mail.subject,
                        "recipient_count": len(mail.recipients)
                    },
                    severity="INFO",
                    username=username
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error withdrawing mail {mail_id}: {e}")
            return False
    
    def _notify_withdrawal(self, mail: Mail):
        """通知邮件撤回"""
        # 在实际应用中，这里可以发送撤回通知
        # 为了简化，我们只记录日志
        self.logger.info(f"Withdrawal notification for mail: {mail.mail_id}")
    
    # ========== 邮件搜索功能 ==========
    
    def search_mails(self, query: str, username: str, domain: str) -> List[Mail]:
        """搜索邮件"""
        
        try:
            # 从存储中获取所有邮件
            inbox_mails = self.storage_manager.get_user_mails(username, domain, "inbox")
            sent_mails = self.storage_manager.get_user_mails(username, domain, "sent")
            
            all_mails = inbox_mails + sent_mails
            
            # 执行搜索
            results = []
            for mail in all_mails:
                if self._matches_search_query(mail, query):
                    results.append(mail)
            
            # 按时间排序（最新的在前）
            results.sort(key=lambda m: m.timestamp, reverse=True)
            
            self.logger.info(f"Search query '{query}' returned {len(results)} results for {username}@{domain}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching mails for {username}@{domain}: {e}")
            return []
    
    def _matches_search_query(self, mail: Mail, query: str) -> bool:
        """检查邮件是否匹配搜索查询"""
        
        if not query:
            return False
        
        query_lower = query.lower()
        
        # 搜索主题
        if query_lower in mail.subject.lower():
            return True
        
        # 搜索正文
        if query_lower in mail.body.lower():
            return True
        
        # 搜索发件人
        if query_lower in mail.sender.full_address.lower():
            return True
        
        # 搜索收件人
        for recipient in mail.recipients:
            if query_lower in recipient.full_address.lower():
                return True
        
        # 搜索CC收件人
        if mail.cc_recipients:
            for recipient in mail.cc_recipients:
                if query_lower in recipient.full_address.lower():
                    return True
        
        return False
    
    # ========== 快速回复功能 ==========
    
    def generate_quick_reply(self, original_mail_id: str, reply_text: str, 
                            username: str, domain: str) -> Optional[Mail]:
        """生成快速回复"""
        
        try:
            # 获取原始邮件
            original_mail = self.storage_manager.get_mail(original_mail_id, username, domain)
            if not original_mail:
                self.logger.error(f"Original mail not found: {original_mail_id}")
                return None
            
            # 创建回复邮件
            reply_subject = f"Re: {original_mail.subject}"
            
            # 添加引用原文
            quoted_body = f"> 原文: {original_mail.sender.full_address} 于 {original_mail.timestamp.strftime('%Y-%m-%d %H:%M')} 写道：\n"
            quoted_body += f"> {original_mail.body[:200]}{'...' if len(original_mail.body) > 200 else ''}\n\n"
            quoted_body += reply_text
            
            # 创建回复邮件对象
            reply_mail = Mail(
                mail_id=f"reply_{original_mail_id}_{int(time.time())}",
                sender=MailAddress(username=username, domain=domain),
                recipients=[original_mail.sender],
                subject=reply_subject,
                body=quoted_body,
                timestamp=datetime.now(),
                status=MailStatus.DRAFT,
                attachments=[]
            )
            
            self.logger.info(f"Generated quick reply for mail: {original_mail_id}")
            return reply_mail
            
        except Exception as e:
            self.logger.error(f"Error generating quick reply: {e}")
            return None
    
    # ========== 后台工作线程 ==========
    
    def _mail_sender_worker(self):
        """邮件发送工作线程"""
        
        self.logger.info("Mail sender worker started")
        
        while True:
            try:
                time.sleep(1)  # 每秒检查一次
                
                with self.queue_lock:
                    if not self.mail_queue:
                        continue
                    
                    # 处理队列中的邮件
                    pending_mails = self.mail_queue.copy()
                    self.mail_queue.clear()
                
                # 发送待处理邮件
                for mail_data in pending_mails:
                    try:
                        mail = mail_data["mail"]
                        token = mail_data.get("token")
                        
                        result = self.send_mail(mail, token)
                        
                        if not result["success"]:
                            self.logger.error(f"Failed to send queued mail {mail.mail_id}: {result.get('error')}")
                            
                    except Exception as e:
                        self.logger.error(f"Error processing queued mail: {e}")
                        
            except Exception as e:
                self.logger.error(f"Error in mail sender worker: {e}")
                time.sleep(5)
    
    def _mail_receiver_worker(self):
        """邮件接收工作线程"""
        
        self.logger.info("Mail receiver worker started")
        
        while True:
            try:
                time.sleep(2)  # 每2秒检查一次
                
                # 检查是否有来自其他服务器的转发邮件
                # 这里可以轮询一个目录或数据库表
                
            except Exception as e:
                self.logger.error(f"Error in mail receiver worker: {e}")
                time.sleep(5)
    
    # ========== 附件处理 ==========
    
    def validate_attachment(self, filename: str, file_path: str) -> Tuple[bool, str]:
        """验证附件"""
        
        try:
            # 检查文件大小
            file_size = Path(file_path).stat().st_size
            is_valid, error_msg = self.security_manager.validate_attachment(filename, file_size)
            
            if not is_valid:
                return False, error_msg
            
            # 检查文件类型
            # 在实际应用中，这里可以添加病毒扫描
            
            return True, ""
            
        except Exception as e:
            return False, f"Attachment validation error: {e}"
    
    def save_attachment(self, filename: str, file_data: bytes, username: str, 
                       domain: str) -> Optional[str]:
        """保存附件"""
        
        try:
            # 生成附件ID
            import hashlib
            import uuid
            
            attachment_id = str(uuid.uuid4())
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # 检查是否已存在相同文件
            existing = self.storage_manager.get_attachment_by_hash(file_hash)
            if existing:
                self.logger.info(f"Attachment already exists: {file_hash}")
                return existing["attachment_id"]
            
            # 保存附件
            attachment_data = {
                "attachment_id": attachment_id,
                "filename": filename,
                "file_hash": file_hash,
                "file_size": len(file_data),
                "uploaded_by": username,
                "domain": domain,
                "upload_time": datetime.now().isoformat()
            }
            
            self.storage_manager.save_attachment(attachment_id, file_data, attachment_data)
            
            self.logger.info(f"Attachment saved: {filename} ({len(file_data)} bytes)")
            return attachment_id
            
        except Exception as e:
            self.logger.error(f"Error saving attachment: {e}")
            return None
    
    # ========== 统计功能 ==========
    
    def get_mail_statistics(self, username: str, domain: str) -> Dict[str, Any]:
        """获取邮件统计信息"""
        
        try:
            inbox_count = len(self.storage_manager.get_user_mails(username, domain, "inbox"))
            sent_count = len(self.storage_manager.get_user_mails(username, domain, "sent"))
            
            # 获取存储使用情况
            storage_usage = self.storage_manager.get_storage_usage(username, domain)
            
            # 获取发送统计
            send_stats = self.security_manager.get_send_statistics(username, domain)
            
            return {
                "inbox_count": inbox_count,
                "sent_count": sent_count,
                "total_count": inbox_count + sent_count,
                "storage_usage_mb": storage_usage,
                "send_statistics": send_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting mail statistics: {e}")
            return {}


if __name__ == "__main__":
    # 测试邮件处理器
    import tempfile
    
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    print("测试邮件处理模块...")
    
    # 创建临时数据目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建存储管理器
    from storage_manager import StorageManager
    storage_manager = StorageManager(temp_dir)
    
    # 创建安全管理器
    config = {
        'encryption_key': 'test_key',
        'jwt_secret': 'test_secret',
        'daily_send_limit': 100,
        'rate_limit_per_minute': 60
    }
    from security import SecurityManager
    security_manager = SecurityManager(config)
    
    # 创建邮件处理器
    mail_handler = MailHandler(storage_manager, security_manager)
    
    print("✓ 邮件处理器创建成功")
    
    # 测试附件验证
    test_file = tempfile.NamedTemporaryFile(delete=False)
    test_file.write(b"Test attachment content")
    test_file.close()
    
    is_valid, error_msg = mail_handler.validate_attachment("test.txt", test_file.name)
    print(f"附件验证: {'通过' if is_valid else f'失败: {error_msg}'}")
    
    # 清理
    import os
    os.unlink(test_file.name)
    
    print("测试完成")