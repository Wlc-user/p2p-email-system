#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gRPC流式客户端演示 - 实时接收推送
"""

import grpc
import logging
import time
from datetime import datetime
from pathlib import Path

# 添加grpc目录到路径
grpc_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(grpc_dir))

from grpc import mail_service_pb2
from grpc import mail_service_pb2_grpc


class GrpcStreamClient:
    """gRPC流式客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 50052):
        self.host = host
        self.port = port
        self.channel: Optional[grpc.Channel] = None
        self.stream_stub: Optional[mail_service_pb2_grpc.MailStreamServiceStub] = None
        self.logger = logging.getLogger("GrpcStreamClient")
    
    def connect(self):
        """连接到流式服务器"""
        try:
            self.channel = grpc.insecure_channel(f'{self.host}:{self.port}')
            self.stream_stub = mail_service_pb2_grpc.MailStreamServiceStub(self.channel)
            
            # 测试连接
            self.logger.info(f"已连接到流式服务器 {self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.channel:
            self.channel.close()
            self.channel = None
            self.stream_stub = None
            self.logger.info("已断开连接")
    
    def receive_new_mail_stream(self, max_count: int = 10):
        """接收新邮件流"""
        self.logger.info("开始接收新邮件推送...")
        print("\n" + "=" * 70)
        print("实时新邮件推送".center(70))
        print("=" * 70)
        
        try:
            # 创建流式请求
            request = mail_service_pb2.PingRequest()
            
            # 接收流式响应
            count = 0
            for notification in self.stream_stub.StreamNewMail(request):
                mail = notification.mail
                
                # 格式化时间
                timestamp = datetime.fromtimestamp(mail.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                
                # 显示邮件
                print(f"\n[新邮件 #{count+1}]")
                print(f"  邮件ID: {mail.mail_id}")
                print(f"  发件人: {mail.sender.username}@{mail.sender.domain}")
                print(f"  主题: {mail.subject}")
                print(f"  时间: {timestamp}")
                print(f"  状态: {mail.status.name}")
                print(f"  内容: {mail.body[:50]}...")
                print("-" * 70)
                
                count += 1
                if count >= max_count:
                    break
            
            print(f"\n[+] 接收完成，共 {count} 封邮件")
            
        except grpc.RpcError as e:
            self.logger.error(f"gRPC错误: {e.code()} - {e.details()}")
        except Exception as e:
            self.logger.error(f"接收失败: {e}")
    
    def receive_mailbox_status_stream(self, duration: int = 30):
        """接收邮箱状态流"""
        self.logger.info(f"开始接收邮箱状态同步 (持续{duration}秒)...")
        print("\n" + "=" * 70)
        print("邮箱状态实时同步".center(70))
        print("=" * 70)
        
        try:
            # 创建流式请求
            request = mail_service_pb2.PingRequest()
            
            start_time = time.time()
            update_count = 0
            
            # 接收流式响应
            for response in self.stream_stub.StreamMailboxStatus(request):
                elapsed = time.time() - start_time
                
                print(f"\n[状态更新 #{update_count+1}] (已运行 {elapsed:.1f}秒)")
                print(f"  消息: {response.message}")
                print(f"  邮件数量: {len(response.mails)}")
                
                # 显示邮件列表
                for i, mail in enumerate(response.mails[:5], 1):
                    print(f"    {i}. {mail.subject}")
                
                if len(response.mails) > 5:
                    print(f"    ... 还有 {len(response.mails) - 5} 封邮件")
                
                print("-" * 70)
                
                update_count += 1
                
                # 检查是否超过持续时间
                if elapsed >= duration:
                    print(f"\n[!] 已达到 {duration} 秒，停止接收")
                    break
            
            print(f"\n[+] 接收完成，共 {update_count} 次状态更新")
            
        except grpc.RpcError as e:
            self.logger.error(f"gRPC错误: {e.code()} - {e.details()}")
        except Exception as e:
            self.logger.error(f"接收失败: {e}")


def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("gRPC流式客户端演示".center(70))
    print("=" * 70)
    print()
    print("本程序演示gRPC的流式传输功能:")
    print("  1. 实时新邮件推送")
    print("  2. 实时邮箱状态同步")
    print()
    
    # 创建客户端
    client = GrpcStreamClient(host="localhost", port=50052)
    
    try:
        # 连接服务器
        if not client.connect():
            print("[-] 连接服务器失败")
            print("\n[!] 请先启动流式服务器:")
            print("    python grpc/grpc_stream_server.py")
            return
        
        print("[+] 连接成功!")
        print()
        
        # 选择功能
        print("请选择要测试的功能:")
        print("  1. 接收新邮件推送")
        print("  2. 接收邮箱状态同步")
        print()
        
        choice = input("请选择 (1-2): ").strip()
        
        if choice == "1":
            # 测试新邮件推送
            print("\n开始接收新邮件推送 (最多10封)...")
            client.receive_new_mail_stream(max_count=10)
            
        elif choice == "2":
            # 测试状态同步
            print("\n开始接收邮箱状态同步 (30秒)...")
            client.receive_mailbox_status_stream(duration=30)
            
        else:
            print("[-] 无效选择")
        
        print("\n[+] 测试完成")
        
    except KeyboardInterrupt:
        print("\n[!] 用户中断")
    finally:
        client.disconnect()
        print("\n[+] 客户端已关闭")


if __name__ == "__main__":
    main()
