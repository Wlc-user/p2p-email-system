#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接启动服务器 - 无需复杂配置
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖"""
    print("[+] 检查依赖...")
    
    required = ['socket', 'threading', 'json', 'logging', 'pathlib']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"    [+] {module}")
        except ImportError:
            print(f"    [-] {module} 缺失")
            missing.append(module)
    
    if missing:
        print(f"\n[-] 缺少必要的模块: {missing}")
        return False
    
    print("    [+] 所有依赖正常")
    return True

def check_config():
    """检查配置文件"""
    print("\n[+] 检查配置文件...")
    
    config_dir = Path("config")
    if not config_dir.exists():
        print("    [-] config 目录不存在")
        return False
    
    configs = ['domain1_config.json', 'domain2_config.json']
    all_ok = True
    
    for config_file in configs:
        config_path = config_dir / config_file
        if config_path.exists():
            print(f"    [+] {config_file}")
        else:
            print(f"    [-] {config_file} 不存在")
            all_ok = False
    
    return all_ok

def check_ports():
    """检查端口"""
    print("\n[+] 检查端口...")
    
    ports = [8080, 8081]
    available = True
    
    for port in ports:
        try:
            import socket
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.bind(('0.0.0.0', port))
            test_socket.close()
            print(f"    [+] 端口 {port} 可用")
        except OSError:
            print(f"    [-] 端口 {port} 已被占用")
            available = False
    
    return available

def start_server():
    """启动服务器"""
    print("\n" + "=" * 70)
    print("启动智能安全邮箱服务器".center(70))
    print("=" * 70)
    print()
    
    # 检查环境
    if not check_dependencies():
        print("\n[-] 依赖检查失败，请安装必要的Python模块")
        return False
    
    if not check_config():
        print("\n[-] 配置文件缺失")
        return False
    
    if not check_ports():
        print("\n[-] 端口冲突")
        print("\n解决方法:")
        print("  1. 停止占用端口的程序")
        print("  2. 修改配置文件中的端口")
        return False
    
    print("\n[+] 环境检查通过")
    print()
    print("服务器信息:")
    print("  Domain 1: example1.com - 端口 8080")
    print("  Domain 2: example2.com - 端口 8081")
    print()
    print("=" * 70)
    print()
    
    # 切换到ant coding目录
    ant_coding_dir = Path(__file__).parent / "ant coding"
    if ant_coding_dir.exists():
        os.chdir(ant_coding_dir)
        print(f"[+] 工作目录: {os.getcwd()}")
    else:
        print(f"[-] 找不到目录: {ant_coding_dir}")
        return False
    
    print()
    print("[*] 正在启动服务器...")
    print("[*] 按 Ctrl+C 停止服务器")
    print()
    
    try:
        # 运行服务器
        result = subprocess.run(
            [sys.executable, "server/main.py"],
            check=False
        )
        
        if result.returncode == 0:
            print("\n[+] 服务器正常退出")
        else:
            print(f"\n[-] 服务器异常退出，代码: {result.returncode}")
        
        return result.returncode == 0
        
    except KeyboardInterrupt:
        print("\n[!] 用户中断")
        return True
    except Exception as e:
        print(f"\n[-] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n智能安全邮箱系统 - 启动器")
    print("=" * 70)
    
    success = start_server()
    
    if success:
        print("\n[+] 程序执行完成")
    else:
        print("\n[-] 启动失败")
    
    print("\n按任意键退出...")
    try:
        input()
    except:
        pass
