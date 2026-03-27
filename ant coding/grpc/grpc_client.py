#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC客户端实现
"""

import grpc
import logging
from typing import List, Optional, Dict
from pathlib import Path

# 添加grpc目录到路径
grpc_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(grpc_dir))

from grpc import mail_service_pb2
from grpc import mail_service_pb2_grpc


class GrpcMailClient:
    """gRPC邮件客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        """
        初始化gRPC客户端
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        self.channel: Optional[grpc.Channel] = None
        self.stub: Optional[mail_service_pb2_grpc.MailServiceStub] = None
        self.token: Optional[str] = None
        self.current_user: Optional[Dict] = None
        
        self.logger = logging.getLogger("GrpcMailClient")
    
    def connect(self):
        """连接到服务器"""
        try:
            self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
            self.stub = mail_service_pb2_grpc.MailServiceStub(self.channel)
            
            # 测试连接
            response = self.stub.Ping(mail_service_pb2.PingRequest())
            if response.success:
                self.logger.info(f"成功连接到服务器 {self.host}:{self.port}")
                return True
            else:
                self.logger.error(f"连接到服务器失败")
                return False
                
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.channel:
            try:
                if self.token:
                    self.logout()
                self.channel.close()
            except:
                pass
            finally:
                self.channel = None
                self.stub = None
                self.token = None
                self.current_user = None
                self.logger.info("已断开连接")
    
    def register(self, username: str, password: str, email: str) -> bool:
        """注册新用户"""
        try:
            request = mail_service_pb2.RegisterRequest(
                username=username,
                password=password,
                email=email
            )
            
            response = self.stub.Register(request)
            
            if response.success:
                self.logger.info(f"用户 {username} 注册成功")
                return True
            else:
                self.logger.error(f"注册失败: {response.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"注册失败: {e}")
            return False
    
    def login(self, username: str, password: str) -> bool:
        """用户登录"""
        try:
            request = mail_service_pb2.LoginRequest(
                username=username,
                password=password,
                client_ip="127.0.0.1"
            )
            
            response = self.stub.Login(request)
            
            if response.success:
                self.token = response.token
                self.current_user = {
                    'username': response.user.username,
                    'email': response.user.email,
                    'domain': response.user.domain
                }
                self.logger.info(f"用户 {username} 登录成功")
                return True
            else:
                self.logger.error(f"登录失败: {response.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            return False
    
    def logout(self) -> bool:
        """用户登出"""
        try:
            if not self.token:
                return True
            
            request = mail_service_pb2.LogoutRequest(token=self.token)
            response = self.stub.Logout(request)
            
            if response.success:
                self.token = None
                self.current_user = None
                self.logger.info("登出成功")
                return True
            else:
                self.logger.error(f"登出失败: {response.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"登出失败: {e}")
            return False
    
    def send_mail(self, to_addresses: List[str], subject: str, body: str,
                  cc: List[str] = None, bcc: List[str] = None) -> Optional[str]:
        """发送邮件"""
        if not self.token:
            self.logger.error("未登录")
            return None
        
        try:
            # 构建邮件对象
            mail = mail_service_pb2.Mail()
            mail.mail_id = f"mail_{hash(subject + str(to_addresses))}"
            mail.subject = subject
            mail.body = body
            mail.timestamp = int(__import__('datetime').datetime.now().timestamp())
            mail.status = mail_service_pb2.MailStatus.SENT
            
            # 设置发件人
            mail.sender.username = self.current_user['username']
            mail.sender.domain = self.current_user['domain']
            
            # 设置收件人
            for address in to_addresses:
                username, domain = address.split('@', 1)
                recipient = mail.recipients.add()
                recipient.username = username
                recipient.domain = domain
            
            # 设置抄送
            if cc:
                for address in cc:
                    username, domain = address.split('@', 1)
                    cc_recipient = mail.cc_recipients.add()
                    cc_recipient.username = username
                    cc_recipient.domain = domain
            
            # 设置密送
            if bcc:
                for address in bcc:
                    username, domain = address.split('@', 1)
                    bcc_recipient = mail.bcc_recipients.add()
                    bcc_recipient.username = username
                    bcc_recipient.domain = domain
            
            request = mail_service_pb2.SendMailRequest(
                token=self.token,
                mail=mail
            )
            
            response = self.stub.SendMail(request)
            
            if response.success:
                self.logger.info(f"邮件发送成功: {response.mail_id}")
                return response.mail_id
            else:
                self.logger.error(f"发送失败: {response.message}")
                return None
                
        except Exception as e:
            self.logger.error(f"发送失败: {e}")
            return None
    
    def get_mailbox(self, mailbox_type: str = "inbox") -> List[Dict]:
        """获取邮箱内容"""
        if not self.token:
            self.logger.error("未登录")
            return []
        
        try:
            request = mail_service_pb2.GetMailboxRequest(
                token=self.token,
                mailbox_type=mailbox_type
            )
            
            response = self.stub.GetMailbox(request)
            
            if response.success:
                mails = []
                for proto_mail in response.mails:
                    mail_dict = {
                        'mail_id': proto_mail.mail_id,
                        'subject': proto_mail.subject,
                        'body': proto_mail.body,
                        'timestamp': __import__('datetime').datetime.fromtimestamp(proto_mail.timestamp),
                        'status': proto_mail.status.name,
                        'sender': {
                            'username': proto_mail.sender.username,
                            'domain': proto_mail.sender.domain
                        },
                        'recipients': [
                            {'username': r.username, 'domain': r.domain}
                            for r in proto_mail.recipients
                        ]
                    }
                    mails.append(mail_dict)
                
                self.logger.info(f"获取到 {len(mails)} 封邮件")
                return mails
            else:
                self.logger.error(f"获取失败: {response.message}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取失败: {e}")
            return []
    
    def withdraw_mail(self, mail_id: str) -> bool:
        """撤回邮件"""
        if not self.token:
            self.logger.error("未登录")
            return False
        
        try:
            request = mail_service_pb2.WithdrawMailRequest(
                token=self.token,
                mail_id=mail_id
            )
            
            response = self.stub.WithdrawMail(request)
            
            if response.success:
                self.logger.info(f"邮件 {mail_id} 撤回成功")
                return True
            else:
                self.logger.error(f"撤回失败: {response.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"撤回失败: {e}")
            return False
    
    def search_mail(self, query: str, search_type: str = "all") -> List[Dict]:
        """搜索邮件"""
        if not self.token:
            self.logger.error("未登录")
            return []
        
        try:
            request = mail_service_pb2.SearchMailRequest(
                token=self.token,
                query=query,
                search_type=search_type
            )
            
            response = self.stub.SearchMail(request)
            
            if response.success:
                results = []
                for proto_mail in response.results:
                    mail_dict = {
                        'mail_id': proto_mail.mail_id,
                        'subject': proto_mail.subject,
                        'body': proto_mail.body,
                        'timestamp': __import__('datetime').datetime.fromtimestamp(proto_mail.timestamp)
                    }
                    results.append(mail_dict)
                
                self.logger.info(f"搜索到 {len(results)} 封邮件")
                return results
            else:
                self.logger.error(f"搜索失败: {response.message}")
                return []
                
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []
    
    def quick_reply(self, original_mail_id: str, reply_text: str) -> bool:
        """快速回复"""
        if not self.token:
            self.logger.error("未登录")
            return False
        
        try:
            request = mail_service_pb2.QuickReplyRequest(
                token=self.token,
                original_mail_id=original_mail_id,
                reply_text=reply_text
            )
            
            response = self.stub.QuickReply(request)
            
            if response.success:
                self.logger.info("快速回复成功")
                return True
            else:
                self.logger.error(f"快速回复失败: {response.message}")
                return False
                
        except Exception as e:
            self.logger.error(f"快速回复失败: {e}")
            return False


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("gRPC邮件客户端测试")
    print("=" * 60)
    
    # 创建客户端
    client = GrpcMailClient(host="localhost", port=50051)
    
    try:
        # 连接服务器
        if not client.connect():
            print("[-] 连接服务器失败")
            exit(1)
        
        print("[+] 连接成功!")
        
        # 注册用户
        print("\n[1] 注册用户...")
        if client.register("testuser", "password123", "testuser@example1.com"):
            print("[+] 注册成功")
        else:
            print("[-] 注册失败（可能用户已存在）")
        
        # 登录
        print("\n[2] 登录...")
        if client.login("testuser", "password123"):
            print("[+] 登录成功")
        else:
            print("[-] 登录失败")
            exit(1)
        
        # 发送邮件
        print("\n[3] 发送邮件...")
        mail_id = client.send_mail(
            to_addresses=["user2@example1.com"],
            subject="测试邮件",
            body="这是一封测试邮件"
        )
        if mail_id:
            print(f"[+] 邮件发送成功: {mail_id}")
        else:
            print("[-] 邮件发送失败")
        
        # 获取邮箱
        print("\n[4] 获取收件箱...")
        mails = client.get_mailbox("inbox")
        print(f"[+] 收件箱中有 {len(mails)} 封邮件")
        for i, mail in enumerate(mails[:3], 1):
            print(f"    {i}. {mail['subject']}")
        
        # 搜索邮件
        print("\n[5] 搜索邮件...")
        results = client.search_mail("测试")
        print(f"[+] 搜索到 {len(results)} 封邮件")
        
        # 登出
        print("\n[6] 登出...")
        client.logout()
        print("[+] 已登出")
        
    except KeyboardInterrupt:
        print("\n[!] 用户中断")
    finally:
        client.disconnect()
        print("\n[+] 客户端已关闭")
