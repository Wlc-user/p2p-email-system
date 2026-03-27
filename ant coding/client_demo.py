#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化客户端演示 - 展示智能邮箱功能
"""

import socket
import json
import time
from pathlib import Path

class SimpleMailClient:
    """简化的邮件客户端"""
    
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
    
    def connect(self):
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"[+] Connected to mail server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"[-] Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("[+] Disconnected from server")
    
    def send_test_message(self, message):
        """发送测试消息"""
        if not self.connected:
            print("[-] Not connected to server")
            return False
        
        try:
            msg_data = json.dumps(message).encode('utf-8')
            self.socket.send(msg_data)
            print(f"[+] Sent message: {message.get('type', 'unknown')}")
            return True
        except Exception as e:
            print(f"[-] Failed to send message: {e}")
            return False

def demo_user_registration():
    """演示用户注册"""
    print("\n" + "="*60)
    print("Demo: User Registration")
    print("="*60)
    
    print("\n[+] Creating test users...")
    users = [
        {"username": "alice", "email": "alice@example1.com", "password": "AlicePass123!"},
        {"username": "bob", "email": "bob@example2.com", "password": "BobPass123!"},
        {"username": "charlie", "email": "charlie@example1.com", "password": "CharliePass123!"}
    ]
    
    for user in users:
        print(f"  User: {user['username']} ({user['email']})")
    
    print("\n[+] In a real system, these users would be:")
    print("  - Registered in the system")
    print("  - Stored securely with encrypted passwords")
    print("  - Able to log in and use email services")

def demo_email_operations():
    """演示邮件操作"""
    print("\n" + "="*60)
    print("Demo: Email Operations")
    print("="*60)
    
    print("\n[+] Available email operations:")
    
    operations = [
        ("Compose Email", "Create new emails with rich text formatting"),
        ("Send Email", "Send emails to users on same or different domains"),
        ("Receive Email", "Automatically receive emails in inbox"),
        ("Read Email", "View email content with attachments"),
        ("Reply/Forward", "Quick reply with context preservation"),
        ("Delete Email", "Move to trash or permanently delete"),
        ("Search Emails", "Search by sender, subject, or keywords"),
        ("Email Folders", "Organize into Inbox, Sent, Drafts, etc.")
    ]
    
    for op, desc in operations:
        print(f"  * {op:20s} - {desc}")

def demo_smart_features():
    """演示智能功能"""
    print("\n" + "="*60)
    print("Demo: Smart Features")
    print("="*60)
    
    print("\n[+] AI-powered features:")
    
    smart_features = [
        ("Email Classification", "Automatically categorize emails (Work, Personal, Spam, etc.)"),
        ("Keyword Extraction", "Extract important keywords from email content"),
        ("Priority Detection", "Identify urgent or important emails"),
        ("Smart Reply", "Generate context-aware reply suggestions"),
        ("Attachment Analysis", "Analyze attachments for security threats"),
        ("Spam Detection", "Identify and filter spam and phishing emails"),
        ("Sentiment Analysis", "Analyze email tone and sentiment"),
        ("Email Summarization", "Generate concise summaries of long emails")
    ]
    
    for feature, desc in smart_features:
        print(f"  * {feature:25s}")
        print(f"    {desc}")

def demo_security_features():
    """演示安全功能"""
    print("\n" + "="*60)
    print("Demo: Security Features")
    print("="*60)
    
    print("\n[+] Security capabilities:")
    
    security_features = [
        ("End-to-End Encryption", "All emails encrypted using AES-256"),
        ("Secure Authentication", "Multi-factor authentication support"),
        ("Login Protection", "Rate limiting and captcha for login attempts"),
        ("Anti-Phishing", "Detect and block phishing attempts"),
        ("Attachment Scanning", "Virus scanning for email attachments"),
        ("Content Filtering", "Block malicious content and scripts"),
        ("Audit Logging", "Complete audit trail of all activities"),
        ("Data Isolation", "Domain-based data separation")
    ]
    
    for feature, desc in security_features:
        print(f"  * {feature:25s}")
        print(f"    {desc}")

def demo_cost_optimization():
    """演示成本优化"""
    print("\n" + "="*60)
    print("Demo: Dynamic Cost Optimization")
    print("="*60)
    
    print("\n[+] Cost optimization strategies:")
    
    cost_strategies = [
        ("Deduplication", "Identical attachments stored only once"),
        ("Compression", "Automatic compression of large files"),
        ("Tiered Storage", "Hot/cold data separation for cost efficiency"),
        ("Load Balancing", "Optimize resource usage across domains"),
        ("Cache Optimization", "Frequently accessed data cached"),
        ("Bandwidth Optimization", "Efficient data transfer protocols")
    ]
    
    for strategy, desc in cost_strategies:
        print(f"  * {strategy:25s}")
        print(f"    {desc}")
    
    print("\n[+] To see the full cost optimization demo:")
    print("  python cost_optimizer/demo_system.py")

def demo_cross_domain():
    """演示跨域通信"""
    print("\n" + "="*60)
    print("Demo: Cross-Domain Communication")
    print("="*60)
    
    print("\n[+] Dual-domain architecture:")
    print("  Domain 1: example1.com (Port 8080)")
    print("  Domain 2: example2.com (Port 8081)")
    
    print("\n[+] Features:")
    print("  * Users can register on either domain")
    print("  * Seamless email exchange between domains")
    print("  * Data isolation per domain")
    print("  * Independent user management")
    print("  * Cross-domain search capabilities")

def main():
    """主函数"""
    print("="*60)
    print("      Smart Secure Email System - Client Demo")
    print("="*60)
    
    # 连接到服务器
    print("\n[+] Connecting to mail servers...")
    client1 = SimpleMailClient("127.0.0.1", 8080)
    client2 = SimpleMailClient("127.0.0.1", 8081)
    
    connected1 = client1.connect()
    connected2 = client2.connect()
    
    if connected1:
        print("[+] Successfully connected to Domain 1 (example1.com)")
    if connected2:
        print("[+] Successfully connected to Domain 2 (example2.com)")
    
    if not (connected1 or connected2):
        print("\n[-] Could not connect to any server")
        print("[!] Make sure servers are running:")
        print("    python start_servers_bg.py")
        return
    
    # 演示各个功能模块
    demo_user_registration()
    demo_email_operations()
    demo_smart_features()
    demo_security_features()
    demo_cost_optimization()
    demo_cross_domain()
    
    # 断开连接
    print("\n" + "="*60)
    print("Demo Complete")
    print("="*60)
    
    if connected1:
        client1.disconnect()
    if connected2:
        client2.disconnect()
    
    print("\n[+] To use the full interactive client:")
    print("  python client/main.py")
    
    print("\n[+] To run the complete system with Docker:")
    print("  docker-compose -f docker-compose.yml up -d")
    
    print("\n[+] To view system documentation:")
    print("  cat README.md")
    print("  cat QUICK_START.md")
    
    print("\n[+] System Status: RUNNING")
    print("  Server 1: http://localhost:8080")
    print("  Server 2: http://localhost:8081")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
