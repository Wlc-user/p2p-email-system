#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC服务器实现
"""

import grpc
import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入gRPC生成的代码
from grpc import mail_service_pb2
from grpc import mail_service_pb2_grpc

# 导入现有模块
from server.mail_handler import MailHandler
from server.storage_manager import StorageManager
from server.security import SecurityManager


class MailServicer(mail_service_pb2_grpc.MailServiceServicer):
    """邮件服务实现"""
    
    def __init__(self, config: Dict, domain: str):
        self.domain = domain
        self.config = config
        self.storage_manager = StorageManager(config['data_path'])
        self.security_manager = SecurityManager(config)
        self.mail_handler = MailHandler(self.storage_manager, self.security_manager)
        
        # 会话管理
        self.active_sessions: Dict[str, Dict] = {}
        
        self.logger = logging.getLogger(f"GrpcServer.{domain}")
    
    def _verify_token(self, token: str) -> Optional[Dict]:
        """验证token并返回用户信息"""
        if not token:
            return None
        
        user_info = self.active_sessions.get(token)
        if user_info:
            return user_info
        
        return None
    
    def _convert_proto_to_mail(self, proto_mail) -> Dict:
        """将protobuf邮件对象转换为字典"""
        return {
            'mail_id': proto_mail.mail_id,
            'sender': {
                'username': proto_mail.sender.username,
                'domain': proto_mail.sender.domain
            },
            'recipients': [
                {'username': r.username, 'domain': r.domain}
                for r in proto_mail.recipients
            ],
            'subject': proto_mail.subject,
            'body': proto_mail.body,
            'timestamp': datetime.fromtimestamp(proto_mail.timestamp),
            'status': proto_mail.status.name,
            'attachments': list(proto_mail.attachments),
            'cc_recipients': [
                {'username': r.username, 'domain': r.domain}
                for r in proto_mail.cc_recipients
            ] if proto_mail.cc_recipients else [],
            'bcc_recipients': [
                {'username': r.username, 'domain': r.domain}
                for r in proto_mail.bcc_recipients
            ] if proto_mail.bcc_recipients else [],
        }
    
    def Register(self, request, context):
        """用户注册"""
        try:
            self.logger.info(f"注册请求: {request.username}")
            
            # 调用现有的注册逻辑
            result = self.mail_handler.register_user(
                request.username,
                request.password,
                request.email
            )
            
            response = mail_service_pb2.RegisterResponse()
            
            if result.get('success'):
                response.success = True
                response.message = "注册成功"
                if 'user' in result:
                    response.user.username = result['user']['username']
                    response.user.email = result['user']['email']
                    response.user.domain = result['user'].get('domain', self.domain)
            else:
                response.success = False
                response.message = result.get('error', '注册失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"注册失败: {e}")
            response = mail_service_pb2.RegisterResponse()
            response.success = False
            response.message = f"注册失败: {str(e)}"
            return response
    
    def Login(self, request, context):
        """用户登录"""
        try:
            self.logger.info(f"登录请求: {request.username}")
            
            # 调用现有的登录逻辑
            result = self.mail_handler.login_user(
                request.username,
                request.password,
                request.client_ip
            )
            
            response = mail_service_pb2.LoginResponse()
            
            if result.get('success'):
                token = str(hash(f"{request.username}_{datetime.now().timestamp()}"))
                self.active_sessions[token] = result.get('user', {})
                
                response.success = True
                response.message = "登录成功"
                response.token = token
                
                if 'user' in result:
                    response.user.username = result['user']['username']
                    response.user.email = result['user']['email']
                    response.user.domain = result['user'].get('domain', self.domain)
            else:
                response.success = False
                response.message = result.get('error', '登录失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            response = mail_service_pb2.LoginResponse()
            response.success = False
            response.message = f"登录失败: {str(e)}"
            return response
    
    def Logout(self, request, context):
        """用户登出"""
        try:
            self.logger.info(f"登出请求: token={request.token[:8]}...")
            
            if request.token in self.active_sessions:
                del self.active_sessions[request.token]
            
            response = mail_service_pb2.LogoutResponse()
            response.success = True
            response.message = "登出成功"
            
            return response
            
        except Exception as e:
            self.logger.error(f"登出失败: {e}")
            response = mail_service_pb2.LogoutResponse()
            response.success = False
            response.message = f"登出失败: {str(e)}"
            return response
    
    def SendMail(self, request, context):
        """发送邮件"""
        try:
            user_info = self._verify_token(request.token)
            if not user_info:
                response = mail_service_pb2.SendMailResponse()
                response.success = False
                response.message = "未授权"
                return response
            
            mail_dict = self._convert_proto_to_mail(request.mail)
            
            # 调用现有的发送邮件逻辑
            result = self.mail_handler.send_mail(
                sender=user_info,
                mail=mail_dict
            )
            
            response = mail_service_pb2.SendMailResponse()
            
            if result.get('success'):
                response.success = True
                response.message = "邮件发送成功"
                response.mail_id = result.get('mail_id')
            else:
                response.success = False
                response.message = result.get('error', '发送失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
            response = mail_service_pb2.SendMailResponse()
            response.success = False
            response.message = f"发送失败: {str(e)}"
            return response
    
    def GetMailbox(self, request, context):
        """获取邮箱内容"""
        try:
            user_info = self._verify_token(request.token)
            if not user_info:
                response = mail_service_pb2.GetMailboxResponse()
                response.success = False
                response.message = "未授权"
                return response
            
            # 调用现有的获取邮箱逻辑
            result = self.mail_handler.get_mailbox(
                username=user_info['username'],
                mailbox_type=request.mailbox_type
            )
            
            response = mail_service_pb2.GetMailboxResponse()
            response.success = True
            response.message = "获取成功"
            
            # 转换邮件列表
            for mail_dict in result.get('mails', []):
                proto_mail = mail_service_pb2.Mail()
                proto_mail.mail_id = mail_dict['mail_id']
                proto_mail.subject = mail_dict['subject']
                proto_mail.body = mail_dict['body']
                proto_mail.timestamp = int(mail_dict['timestamp'].timestamp())
                proto_mail.status = mail_service_pb2.MailStatus.Value(mail_dict['status'])
                
                # 设置发件人
                sender = proto_mail.sender
                sender.username = mail_dict['sender']['username']
                sender.domain = mail_dict['sender']['domain']
                
                # 设置收件人
                for recipient in mail_dict['recipients']:
                    proto_recipient = proto_mail.recipients.add()
                    proto_recipient.username = recipient['username']
                    proto_recipient.domain = recipient['domain']
                
                response.mails.append(proto_mail)
            
            return response
            
        except Exception as e:
            self.logger.error(f"获取邮箱失败: {e}")
            response = mail_service_pb2.GetMailboxResponse()
            response.success = False
            response.message = f"获取失败: {str(e)}"
            return response
    
    def WithdrawMail(self, request, context):
        """撤回邮件"""
        try:
            user_info = self._verify_token(request.token)
            if not user_info:
                response = mail_service_pb2.WithdrawMailResponse()
                response.success = False
                response.message = "未授权"
                return response
            
            # 调用现有的撤回邮件逻辑
            result = self.mail_handler.withdraw_mail(
                username=user_info['username'],
                mail_id=request.mail_id
            )
            
            response = mail_service_pb2.WithdrawMailResponse()
            
            if result.get('success'):
                response.success = True
                response.message = "邮件撤回成功"
            else:
                response.success = False
                response.message = result.get('error', '撤回失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"撤回邮件失败: {e}")
            response = mail_service_pb2.WithdrawMailResponse()
            response.success = False
            response.message = f"撤回失败: {str(e)}"
            return response
    
    def SearchMail(self, request, context):
        """搜索邮件"""
        try:
            user_info = self._verify_token(request.token)
            if not user_info:
                response = mail_service_pb2.SearchMailResponse()
                response.success = False
                response.message = "未授权"
                return response
            
            # 调用现有的搜索邮件逻辑
            result = self.mail_handler.search_mail(
                username=user_info['username'],
                query=request.query,
                search_type=request.search_type
            )
            
            response = mail_service_pb2.SearchMailResponse()
            response.success = True
            response.message = "搜索成功"
            
            # 转换搜索结果
            for mail_dict in result.get('results', []):
                proto_mail = mail_service_pb2.Mail()
                proto_mail.mail_id = mail_dict['mail_id']
                proto_mail.subject = mail_dict['subject']
                proto_mail.body = mail_dict['body']
                proto_mail.timestamp = int(mail_dict['timestamp'].timestamp())
                
                response.results.append(proto_mail)
            
            return response
            
        except Exception as e:
            self.logger.error(f"搜索邮件失败: {e}")
            response = mail_service_pb2.SearchMailResponse()
            response.success = False
            response.message = f"搜索失败: {str(e)}"
            return response
    
    def QuickReply(self, request, context):
        """快速回复"""
        try:
            user_info = self._verify_token(request.token)
            if not user_info:
                response = mail_service_pb2.QuickReplyResponse()
                response.success = False
                response.message = "未授权"
                return response
            
            # 调用现有的快速回复逻辑
            result = self.mail_handler.quick_reply(
                username=user_info['username'],
                original_mail_id=request.original_mail_id,
                reply_text=request.reply_text
            )
            
            response = mail_service_pb2.QuickReplyResponse()
            
            if result.get('success'):
                response.success = True
                response.message = "快速回复成功"
            else:
                response.success = False
                response.message = result.get('error', '快速回复失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"快速回复失败: {e}")
            response = mail_service_pb2.QuickReplyResponse()
            response.success = False
            response.message = f"快速回复失败: {str(e)}"
            return response
    
    def GroupSend(self, request, context):
        """群发邮件"""
        try:
            user_info = self._verify_token(request.token)
            if not user_info:
                response = mail_service_pb2.GroupSendResponse()
                response.success = False
                response.message = "未授权"
                return response
            
            mail_dict = self._convert_proto_to_mail(request.mail)
            
            # 调用现有的群发邮件逻辑
            result = self.mail_handler.group_send(
                sender=user_info,
                group_id=request.group_id,
                mail=mail_dict
            )
            
            response = mail_service_pb2.GroupSendResponse()
            
            if result.get('success'):
                response.success = True
                response.message = "群发邮件成功"
                response.mail_id = result.get('mail_id')
                response.recipient_count = result.get('recipient_count', 0)
            else:
                response.success = False
                response.message = result.get('error', '群发失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"群发邮件失败: {e}")
            response = mail_service_pb2.GroupSendResponse()
            response.success = False
            response.message = f"群发失败: {str(e)}"
            return response
    
    def Ping(self, request, context):
        """心跳检测"""
        response = mail_service_pb2.PongResponse()
        response.success = True
        response.message = "pong"
        return response
    
    def ForwardMail(self, request, context):
        """转发邮件（服务器间）"""
        try:
            # 调用现有的转发邮件逻辑
            result = self.mail_handler.forward_mail(
                mail=self._convert_proto_to_mail(request.mail),
                target_domain=request.target_domain
            )
            
            response = mail_service_pb2.ForwardMailResponse()
            
            if result.get('success'):
                response.success = True
                response.message = "邮件转发成功"
            else:
                response.success = False
                response.message = result.get('error', '转发失败')
            
            return response
            
        except Exception as e:
            self.logger.error(f"转发邮件失败: {e}")
            response = mail_service_pb2.ForwardMailResponse()
            response.success = False
            response.message = f"转发失败: {str(e)}"
            return response


def serve(config: Dict, domain: str, port: int):
    """启动gRPC服务器"""
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    
    # 添加服务
    mail_service = MailServicer(config, domain)
    mail_service_pb2_grpc.add_MailServiceServicer_to_server(mail_service, server)
    
    # 绑定端口
    server.add_insecure_port(f'[::]:{port}')
    
    # 启动服务器
    server.start()
    logging.info(f"gRPC服务器启动成功: {domain} - 端口 {port}")
    
    return server


if __name__ == "__main__":
    import sys
    import json
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    if len(sys.argv) > 2:
        config_path = sys.argv[1]
        domain = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 50051
    else:
        config_path = "config/domain1_config.json"
        domain = "example1.com"
        port = 50051
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 启动服务器
    server = serve(config, domain, port)
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("服务器停止")
        server.stop(0)
