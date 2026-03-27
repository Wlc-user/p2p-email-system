#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速启动服务器脚本
"""

import os
import sys
import subprocess
from pathlib import Path

# 获取ant coding目录
ant_coding_dir = Path(__file__).parent / "ant coding"

if not ant_coding_dir.exists():
    print(f"[错误] 找不到目录: {ant_coding_dir}")
    sys.exit(1)

os.chdir(ant_coding_dir)

print("[+] 工作目录:", os.getcwd())
print("[+] 正在启动邮箱服务器...")
print("[+]")

try:
    # 启动服务器
    process = subprocess.Popen(
        [sys.executable, "server/main.py"],
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )
    
    print(f"[+] 服务器已启动, PID: {process.pid}")
    print(f"[+] 域名1: http://localhost:8080 (example1.com)")
    print(f"[+] 域名2: http://localhost:8081 (example2.com)")
    print(f"[+]")
    print(f"[!] 按任意键停止服务器...")
    print(f"[!] 或者使用命令: taskkill /PID {process.pid} /F")
    print()
    
    import time
    time.sleep(2)
    
    # 检查服务器是否仍在运行
    if process.poll() is None:
        print("[+] 服务器运行正常")
        input("\n按回车键停止服务器...")
        process.terminate()
        process.wait(timeout=5)
        print("[+] 服务器已停止")
    else:
        print(f"[-] 服务器已停止, 退出码: {process.returncode}")
        
except KeyboardInterrupt:
    print("\n[!] 用户中断")
except Exception as e:
    print(f"[-] 错误: {e}")
