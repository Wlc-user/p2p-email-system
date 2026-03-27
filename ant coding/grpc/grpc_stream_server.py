#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC流式服务器实现 - 支持实时推送和流式传输
"""

import grpc
import logging
import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from datetime import datetime
import json

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

# 导入gRPC生成的代码
from grpc import mail_service_pb2
from grpc import mail_service_pb2_grpc

# 导入现有模块
from server.mail_handler import MailHandler
from server.storage_manager import StorageManager
from server.security import SecurityManager


class MailStreamServicer(mail_service_pb2_grpc.MailStreamServiceServicer):
    """流式邮件服务实现"""
    
    def __init__(self, config: Dict, domain: str):
        self.domain = domain
        self.config = config
        self.storage_manager = StorageManager(config['data_path'])
        self.security_manager = SecurityManager(config)
        self.mail_handler = MailHandler(self.storage_manager, self.security_manager)
        
        # 流式通知队列
        self.notification_queues: Dict[str, Queue] = {}
        self.lock = threading.Lock()
        
        self.logger = logging.getLogger(f"GrpcStreamServer.{domain}")
    
    def StreamNewMail(self, request, context):
        """流式接收新邮件通知"""
        self.logger.info("客户端连接到新邮件流")
        
        # 为这个连接创建队列
        client_id = f"{context.peer()}_{time.time()}"
        with self.lock:
            self.notification_queues[client_id] = Queue(maxsize=100)
        
        try:
            # 模拟新邮件推送
            for i in range(10):
                # 检查连接是否还活跃
                if context.is_active():
                    # 创建模拟新邮件通知
                    notification = mail_service_pb2.NewMailNotification()
                    
                    mail = notification.mail
                    mail.mail_id = f"stream_mail_{i}_{int(time.time())}"
                    mail.subject = f"实时推送邮件 {i+1}"
                    mail.body = f"这是一封通过流式传输推送的邮件，时间戳: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    mail.timestamp = int(time.time())
                    mail.status = mail_service_pb2.MailStatus.DELIVERED
                    
                    # 设置发件人
                    mail.sender.username = "system"
                    mail.sender.domain = self.domain
                    
                    # 设置收件人
                    recipient = mail.recipients.add()
                    recipient.username = "user"
                    recipient.domain = self.domain
                    
                    notification.timestamp = int(time.time())
                    
                    self.logger.info(f"推送新邮件: {mail.mail_id}")
                    yield notification
                    
                    # 每隔3秒推送一次
                    time.sleep(3)
                else:
                    self.logger.info("客户端断开连接")
                    break
                    
        except Exception as e:
            self.logger.error(f"流式传输错误: {e}")
        finally:
            # 清理队列
            with self.lock:
                if client_id in self.notification_queues:
                    del self.notification_queues[client_id]
            self.logger.info("新邮件流结束")
    
    def StreamMailboxStatus(self, request, context):
        """流式同步邮箱状态"""
        self.logger.info("客户端连接到邮箱状态流")
        
        try:
            while context.is_active():
                # 获取当前邮箱状态
                response = mail_service_pb2.GetMailboxResponse()
                response.success = True
                response.message = f"状态更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
                # 添加模拟邮件
                for i in range(3):
                    mail = response.mails.add()
                    mail.mail_id = f"status_{i}_{int(time.time())}"
                    mail.subject = f"状态邮件 {i+1}"
                    mail.body = f"邮箱状态同步邮件 {i+1}"
                    mail.timestamp = int(time.time())
                    mail.status = mail_service_pb2.MailStatus.READ
                    
                    mail.sender.username = "system"
                    mail.sender.domain = self.domain
                
                self.logger.info("推送邮箱状态")
                yield response
                
                # 每隔5秒推送一次状态更新
                time.sleep(5)
                
        except Exception as e:
            self.logger.error(f"状态流错误: {e}")
        
        self.logger.info("邮箱状态流结束")
    
    def push_new_mail(self, mail_dict: Dict):
        """推送新邮件到所有连接的客户端"""
        notification = mail_service_pb2.NewMailNotification()
        
        mail = notification.mail
        mail.mail_id = mail_dict.get('mail_id', '')
        mail.subject = mail_dict.get('subject', '')
        mail.body = mail_dict.get('body', '')
        
        if isinstance(mail_dict.get('timestamp'), datetime):
            mail.timestamp = int(mail_dict['timestamp'].timestamp())
        else:
            mail.timestamp = int(time.time())
        
        mail.status = mail_service_pb2.MailStatus.DELIVERED
        
        # 设置发件人
        sender_info = mail_dict.get('sender', {})
        mail.sender.username = sender_info.get('username', '')
        mail.sender.domain = sender_info.get('domain', '')
        
        # 设置收件人
        for recipient_info in mail_dict.get('recipients', []):
            recipient = mail.recipients.add()
            recipient.username = recipient_info.get('username', '')
            recipient.domain = recipient_info.get('domain', '')
        
        notification.timestamp = int(time.time())
        
        # 推送到所有队列
        with self.lock:
            for client_id, queue in self.notification_queues.items():
                if queue.full():
                    queue.get()  # 移除最旧的通知
                queue.put(notification)
        
        self.logger.info(f"新邮件已推送到 {len(self.notification_queues)} 个客户端")


class GrpcStreamServer:
    """gRPC流式服务器"""
    
    def __init__(self, config: Dict, domain: str, port: int):
        self.config = config
        self.domain = domain
        self.port = port
        self.stream_servicer = MailStreamServicer(config, domain)
        self.server = None
        
        self.logger = logging.getLogger(f"GrpcStreamServer.{domain}")
    
    def start(self):
        """启动流式服务器"""
        try:
            # 创建服务器
            self.server = grpc.server(ThreadPoolExecutor(max_workers=10))
            
            # 添加流式服务
            mail_service_pb2_grpc.add_MailStreamServiceServicer_to_server(
                self.stream_servicer, self.server
            )
            
            # 绑定端口
            self.server.add_insecure_port(f'[::]:{self.port}')
            
            # 启动服务器
            self.server.start()
            self.logger.info(f"gRPC流式服务器启动: {domain} - 端口 {self.port}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动失败: {e}")
            return False
    
    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.stop(0)
            self.logger.info("服务器已停止")
    
    def wait_for_termination(self):
        """等待服务器终止"""
        if self.server:
            self.server.wait_for_termination()


def main():
    """主函数"""
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    if len(sys.argv) > 2:
        config_path = sys.argv[1]
        domain = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 50052
    else:
        config_path = "config/domain1_config.json"
        domain = "example1.com"
        port = 50052
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 创建并启动流式服务器
    server = GrpcStreamServer(config, domain, port)
    
    if server.start():
        print(f"\n[+] gRPC流式服务器已启动!")
        print(f"[+] 域名: {domain}")
        print(f"[+] 端口: {port}")
        print(f"[+] 流式接口:")
        print(f"     - StreamNewMail: 实时新邮件推送")
        print(f"     - StreamMailboxStatus: 实时邮箱状态同步")
        print(f"\n[!] 按 Ctrl+C 停止服务器")
        print("=" * 60)
        
        try:
            server.wait_for_termination()
        except KeyboardInterrupt:
            print("\n[!] 正在停止服务器...")
            server.stop()
            print("[+] 服务器已停止")
    else:
        print("[-] 服务器启动失败")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
