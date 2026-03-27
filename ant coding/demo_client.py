#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能邮箱系统演示脚本
"""

import sys
import socket
import json
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from server.protocols import Message, MessageType, Mail, MailAddress, MailStatus

class MailDemoClient:
    """演示客户端"""
    
    def __init__(self, host='127.0.0.1', port=8080):
        self.host = host
        self.port = port
        self.socket = None
    
    def connect(self):
        """连接服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            print(f"[+] Connected to server {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[-] Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            try:
                self.socket.close()
                print("[+] Disconnected from server")
            except:
                pass
    
    def send_message(self, message):
        """发送消息"""
        try:
            data = json.dumps(message.to_dict(), ensure_ascii=False)
            self.socket.sendall(data.encode('utf-8') + b'\n')
            print(f"[+] Sent message: {message.message_type.name}")
            return True
        except Exception as e:
            print(f"[-] Failed to send message: {e}")
            return False
    
    def receive_message(self):
        """接收消息"""
        try:
            data = self.socket.recv(4096)
            if data:
                msg_dict = json.loads(data.decode('utf-8'))
                return Message.from_dict(msg_dict)
        except Exception as e:
            print(f"[-] Failed to receive message: {e}")
        return None
    
    def test_basic_operations(self):
        """测试基本操作"""
        print("\n" + "=" * 60)
        print("Testing Basic Operations")
        print("=" * 60)
        
        # 测试注册
        print("\n[1] Testing user registration...")
        register_msg = Message.create(
            message_type=MessageType.REGISTER,
            payload={
                "username": "demo_user",
                "password": "Demo@123",
                "email": "demo@example1.com"
            }
        )
        
        if self.send_message(register_msg):
            response = self.receive_message()
            if response:
                print(f"[+] Registration response: {response.payload}")
        
        time.sleep(1)
        
        # 测试登录
        print("\n[2] Testing user login...")
        login_msg = Message.create(
            message_type=MessageType.LOGIN,
            payload={
                "username": "demo_user",
                "password": "Demo@123"
            }
        )
        
        if self.send_message(login_msg):
            response = self.receive_message()
            if response:
                print(f"[+] Login response: {response.payload}")
                return response.payload.get('success', False)
        
        return False
    
    def test_send_mail(self):
        """测试发送邮件"""
        print("\n" + "=" * 60)
        print("Testing Mail Sending")
        print("=" * 60)
        
        # 创建测试邮件
        from_addr = MailAddress("demo", "example1.com")
        to_addr = MailAddress("admin", "example1.com")
        
        mail = Mail(
            mail_id=str(time.time()),
            sender=from_addr,
            recipients=[to_addr],
            subject="Test Email from Demo Client",
            body="This is a test email sent from the demo client.",
            timestamp=datetime.now(),
            status=MailStatus.DRAFT
        )
        
        print(f"\n[+] Creating mail: {mail.subject}")
        print(f"    From: {mail.sender.full_address}")
        print(f"    To: {mail.recipients[0].full_address}")
        print(f"    Body: {mail.body}")
        
        # 发送邮件
        send_mail_msg = Message.create(
            message_type=MessageType.SEND_MAIL,
            payload={"mail": mail.to_dict()}
        )
        
        if self.send_message(send_mail_msg):
            response = self.receive_message()
            if response:
                print(f"\n[+] Send mail response: {response.payload}")
                return response.payload.get('success', False)
        
        return False

def main():
    """主函数"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  Smart Secure Email System - Demo  ".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    print()
    
    # 测试域名1
    print("\n" + "=" * 60)
    print("Testing Domain 1 Server (example1.com:8080)")
    print("=" * 60)
    
    client1 = MailDemoClient('127.0.0.1', 8080)
    
    if client1.connect():
        # 测试基本操作
        success = client1.test_basic_operations()
        
        if success:
            # 测试发送邮件
            client1.test_send_mail()
        
        client1.disconnect()
    else:
        print("[-] Cannot connect to server. Make sure the server is running.")
        print("    Run: python server/main.py")
        return 1
    
    # 测试域名2
    print("\n" + "=" * 60)
    print("Testing Domain 2 Server (example2.com:8081)")
    print("=" * 60)
    
    client2 = MailDemoClient('127.0.0.1', 8081)
    
    if client2.connect():
        print("[+] Domain 2 server is also running")
        client2.disconnect()
    else:
        print("[-] Domain 2 server is not running")
    
    # 显示总结
    print("\n" + "=" * 60)
    print("Demo Summary")
    print("=" * 60)
    print()
    print("[+] Smart Secure Email System is running!")
    print()
    print("Server Information:")
    print("  - Domain 1 (example1.com): http://localhost:8080")
    print("  - Domain 2 (example2.com): http://localhost:8081")
    print()
    print("System Features:")
    print("  - Dual-domain mail servers")
    print("  - User registration and authentication")
    print("  - Mail sending and receiving")
    print("  - Security and encryption")
    print("  - Intelligent mail classification")
    print("  - Cost optimization")
    print()
    print("Next Steps:")
    print("  1. Explore the code in server/ and client/ directories")
    print("  2. Check configuration in config/ directory")
    print("  3. View logs in logs/ directory")
    print("  4. Run cost optimizer demo: python cost_optimizer/demo_system.py")
    print("  5. Try Docker deployment: docker-compose up")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[!] Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
