#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试 - 验证服务器基本功能
"""

import socket
import time
import json
from threading import Thread

def test_server_connection(port, domain):
    """测试服务器连接"""
    print(f"\n[+] Testing connection to {domain} (port {port})...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"[+] {domain} is reachable on port {port}")
            return True
        else:
            print(f"[-] {domain} is NOT reachable on port {port}")
            return False
            
    except Exception as e:
        print(f"[-] Error connecting to {domain}: {e}")
        return False

def test_basic_operations():
    """测试基本操作"""
    print("\n" + "="*60)
    print("Testing Basic Server Operations")
    print("="*60)
    
    # 测试端口连接
    results = []
    results.append(test_server_connection(8080, "example1.com"))
    results.append(test_server_connection(8081, "example2.com"))
    
    # 测试数据目录
    print("\n[+] Checking data directories...")
    from pathlib import Path
    
    data_dirs = [
        "data/domain1",
        "data/domain2",
        "logs"
    ]
    
    for dir_path in data_dirs:
        path = Path(dir_path)
        if path.exists():
            files = list(path.glob("*"))
            print(f"[+] {dir_path}: {len(files)} files/folders")
        else:
            print(f"[-] {dir_path}: NOT exists")
    
    # 总结
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    if all(results):
        print("[+] All server connection tests PASSED")
        return True
    else:
        print("[-] Some tests FAILED")
        return False

def demo_mail_operations():
    """演示邮件操作"""
    print("\n" + "="*60)
    print("Demo: Mail Operations")
    print("="*60)
    
    print("\n[+] Available operations:")
    print("  1. User registration")
    print("  2. User login")
    print("  3. Send email")
    print("  4. Receive email")
    print("  5. Search emails")
    print("  6. Smart classification")
    print("  7. Attachment handling")
    print("  8. Security features")
    
    print("\n[+] To test these operations, use the client:")
    print("  python client/main.py")
    
    print("\n[+] Server endpoints:")
    print("  Domain 1: localhost:8080")
    print("  Domain 2: localhost:8081")

def main():
    """主函数"""
    print("="*60)
    print("      Smart Secure Email System - Quick Test")
    print("="*60)
    
    # 等待服务器启动
    print("\n[+] Waiting for servers to start...")
    time.sleep(2)
    
    # 运行基本测试
    test_result = test_basic_operations()
    
    # 演示邮件操作
    demo_mail_operations()
    
    # 最终总结
    print("\n" + "="*60)
    print("Final Summary")
    print("="*60)
    
    if test_result:
        print("\n[+] SUCCESS: System is running!")
        print("[+] Servers are online and accepting connections")
        print("[+] Next steps:")
        print("  1. Run client: python client/main.py")
        print("  2. Register a user")
        print("  3. Send and receive emails")
        print("  4. Try smart features")
    else:
        print("\n[-] WARNING: Some servers may not be running")
        print("[!] Check the logs: logs/dual_server.log")
    
    print("\n[+] For Docker deployment:")
    print("  docker-compose -f docker-compose.yml up -d")
    print("  docker-compose -f docker-compose-simple.yml up -d")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
