#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
在后台启动服务器
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_servers_background():
    """在后台启动服务器"""
    print("[+] Starting mail servers in background...")
    
    # 切换到项目目录
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # 启动服务器
    try:
        # 在Windows上使用CREATE_NEW_PROCESS_GROUP
        if sys.platform == "win32":
            process = subprocess.Popen(
                [sys.executable, "server/main.py"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            process = subprocess.Popen([sys.executable, "server/main.py"])
        
        print(f"[+] Server process started with PID: {process.pid}")
        print(f"[+] Domain 1: http://localhost:8080")
        print(f"[+] Domain 2: http://localhost:8081")
        print(f"[+] Logs directory: logs/")
        print(f"\n[!] Servers are running in background")
        print(f"[!] Press Ctrl+C to stop (if running in foreground)")
        print(f"[!] Or run: kill {process.pid}")
        
        return process
        
    except Exception as e:
        print(f"[-] Failed to start servers: {e}")
        return None

if __name__ == "__main__":
    process = start_servers_background()
    
    if process:
        try:
            # 等待几秒钟确认启动
            time.sleep(5)
            print("\n[+] Servers should be running now")
            
            # 检查进程状态
            if process.poll() is None:
                print(f"[+] Process {process.pid} is still running")
            else:
                print(f"[-] Process {process.pid} has stopped")
                print(f"[-] Exit code: {process.returncode}")
            
        except KeyboardInterrupt:
            print("\n[!] Interrupted by user")
            try:
                process.terminate()
                process.wait(timeout=5)
                print("[+] Server process terminated")
            except Exception as e:
                print(f"[-] Error terminating process: {e}")
