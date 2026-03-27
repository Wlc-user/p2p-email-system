#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动智能安全邮箱系统的双服务器
"""

import subprocess
import sys
import time
import os
import threading
from pathlib import Path

def start_server(domain: str, port: int):
    """启动单个邮箱服务器"""
    print(f"🚀 启动 {domain} 邮箱服务器 (端口: {port})...")
    
    # 创建数据目录
    data_dir = Path(f"data/{domain.replace('.com', '')}")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建日志目录
    log_dir = Path(f"logs/{domain.replace('.com', '')}")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 启动服务器
    cmd = [
        sys.executable, "server/main.py",
        "--domain", domain,
        "--port", str(port),
        "--log-level", "INFO"
    ]
    
    try:
        # 在新窗口中启动服务器
        if sys.platform == "win32":
            # Windows: 使用 start 命令在新控制台窗口启动
            process = subprocess.Popen(
                ["start", "cmd", "/k", sys.executable, "server/main.py", 
                 "--domain", domain, "--port", str(port), "--log-level", "INFO"],
                shell=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Linux/Mac: 使用 xterm 或 gnome-terminal
            process = subprocess.Popen(
                cmd,
                stdout=open(f"logs/{domain.replace('.com', '')}/server.log", "w"),
                stderr=subprocess.STDOUT,
                text=True
            )
        
        return process
    except Exception as e:
        print(f"❌ 启动服务器 {domain} 失败: {e}")
        return None

def check_server_status(domain: str, port: int, timeout=30):
    """检查服务器状态"""
    import socket
    import time
    
    print(f"⏳ 检查 {domain}:{port} 服务器状态...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"✅ {domain} 服务器已启动并运行在端口 {port}")
                return True
            else:
                print(f"⏳ {domain} 服务器仍在启动中...")
                time.sleep(2)
        except Exception as e:
            print(f"⚠️  检查 {domain} 状态时出错: {e}")
            time.sleep(2)
    
    print(f"❌ {domain} 服务器启动超时")
    return False

def main():
    """主函数"""
    print("=" * 60)
    print("      智能安全邮箱系统 - 服务器启动器")
    print("=" * 60)
    print()
    print("📧 系统配置:")
    print("  • 域名1: example1.com (端口: 8080)")
    print("  • 域名2: example2.com (端口: 8081)")
    print("  • 数据隔离: 独立存储目录")
    print("  • 安全特性: 完整的安全模块")
    print()
    
    # 检查Python依赖
    print("🔍 检查依赖...")
    try:
        import cryptography
        import flask
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 启动服务器
    print()
    print("🔄 启动服务器...")
    
    # 启动第一个服务器
    server1 = start_server("example1.com", 8080)
    time.sleep(3)  # 给第一个服务器启动时间
    
    # 启动第二个服务器
    server2 = start_server("example2.com", 8081)
    
    # 检查服务器状态
    print()
    print("🔍 验证服务器状态...")
    
    status1 = check_server_status("example1.com", 8080)
    status2 = check_server_status("example2.com", 8081)
    
    if status1 and status2:
        print()
        print("=" * 60)
        print("🎉 服务器启动成功!")
        print("=" * 60)
        print()
        print("📊 服务器状态:")
        print(f"  ✅ example1.com: http://localhost:8080")
        print(f"  ✅ example2.com: http://localhost:8081")
        print()
        print("🔗 API端点:")
        print("  • 健康检查: /api/health")
        print("  • 用户注册: /api/register")
        print("  • 用户登录: /api/login")
        print("  • 发送邮件: /api/mail/send")
        print("  • 接收邮件: /api/mail/inbox")
        print()
        print("🚀 接下来可以:")
        print("  1. 运行客户端: python client/main.py")
        print("  2. 运行测试: python integration_test.py")
        print("  3. 停止服务器: 按 Ctrl+C")
        
        try:
            # 保持主程序运行
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 停止服务器...")
            if server1:
                server1.terminate()
            if server2:
                server2.terminate()
            print("✅ 服务器已停止")
    else:
        print("❌ 服务器启动失败，请检查日志")
        if server1:
            server1.terminate()
        if server2:
            server2.terminate()

if __name__ == "__main__":
    main()