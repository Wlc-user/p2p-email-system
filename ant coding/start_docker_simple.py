#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker快速启动脚本
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_docker():
    """检查Docker是否安装"""
    print("[+] Checking Docker installation...")
    
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"[+] {result.stdout.strip()}")
            return True
        else:
            print("[-] Docker is not installed")
            return False
    except Exception as e:
        print(f"[-] Error checking Docker: {e}")
        return False

def check_docker_compose():
    """检查Docker Compose是否安装"""
    print("\n[+] Checking Docker Compose...")
    
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print(f"[+] {result.stdout.strip()}")
            return True
        else:
            print("[-] Docker Compose is not installed")
            return False
    except Exception as e:
        print(f"[-] Error checking Docker Compose: {e}")
        return False

def create_docker_file():
    """创建简化的Dockerfile"""
    dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data/domain1 /app/data/domain2 /app/logs

# 暴露端口
EXPOSE 8080 8081

# 启动命令
CMD ["python", "server/main.py"]
'''
    
    dockerfile_path = Path("Dockerfile")
    if not dockerfile_path.exists():
        with open(dockerfile_path, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        print("[+] Created Dockerfile")
    else:
        print("[+] Dockerfile already exists")

def start_docker_simple():
    """使用简化版docker-compose启动"""
    print("\n[+] Starting services with Docker Compose (simple)...")
    
    try:
        # 使用简化版配置
        compose_file = "docker-compose-simple.yml"
        
        # 启动服务
        subprocess.run(['docker-compose', '-f', compose_file, 'up', '-d'], shell=True)
        
        print("\n[+] Docker services are starting...")
        print("[+] Wait a few seconds for services to be ready...")
        
        # 等待服务启动
        time.sleep(5)
        
        # 检查服务状态
        print("\n[+] Checking service status...")
        subprocess.run(['docker-compose', '-f', compose_file, 'ps'], shell=True)
        
        print("\n[+] Services should be accessible at:")
        print("  - Server 1: http://localhost:8080")
        print("  - Server 2: http://localhost:8081")
        
        print("\n[+] To view logs:")
        print(f"  docker-compose -f {compose_file} logs -f")
        
        print("\n[+] To stop services:")
        print(f"  docker-compose -f {compose_file} down")
        
        return True
        
    except Exception as e:
        print(f"[-] Failed to start Docker services: {e}")
        return False

def stop_docker():
    """停止Docker服务"""
    print("\n[+] Stopping Docker services...")
    
    try:
        subprocess.run(['docker-compose', 'down'], shell=True)
        print("[+] Docker services stopped")
        return True
    except Exception as e:
        print(f"[-] Error stopping services: {e}")
        return False

def show_docker_info():
    """显示Docker信息"""
    print("\n[+] Docker deployment info:")
    
    print("""
Docker deployment provides:
  - Containerized environment
  - Easy deployment and scaling
  - Isolated dependencies
  - Consistent runtime environment
  - Easy rollback and updates

Available compose files:
  - docker-compose.yml       (Full deployment with tests)
  - docker-compose-simple.yml (Simplified deployment)

Commands:
  docker-compose up -d              (Start services)
  docker-compose down                (Stop services)
  docker-compose logs -f             (View logs)
  docker-compose ps                  (Check status)
  docker-compose exec <container> bash (Access container)
""")

def main():
    """主函数"""
    print("="*60)
    print("      Smart Secure Email System - Docker Deployment")
    print("="*60)
    
    # 检查Docker
    if not check_docker():
        print("\n[-] Docker is not installed or not accessible")
        print("[!] Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return
    
    if not check_docker_compose():
        print("\n[-] Docker Compose is not installed")
        print("[!] Docker Compose is usually included with Docker Desktop")
        return
    
    # 显示信息
    show_docker_info()
    
    # 创建必要的文件
    create_docker_file()
    
    # 提供选项
    print("\n[+] Options:")
    print("  1. Start services with Docker (Simple)")
    print("  2. Start services with Docker (Full)")
    print("  3. Stop running services")
    print("  4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == '1':
        start_docker_simple()
    elif choice == '2':
        print("\n[+] Starting full deployment...")
        subprocess.run(['docker-compose', 'up', '-d'], shell=True)
    elif choice == '3':
        stop_docker()
    elif choice == '4':
        print("[+] Exiting...")
    else:
        print("[-] Invalid choice")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[+] Interrupted by user")
    except Exception as e:
        print(f"[-] Error: {e}")
