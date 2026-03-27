#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查运行环境 - 简化版
"""

import sys
import os
import subprocess
import platform

def check_python():
    """检查Python环境"""
    print("[-] Checking Python environment...")
    
    try:
        python_version = platform.python_version()
        python_executable = sys.executable
        
        print(f"[+] Python version: {python_version}")
        print(f"[+] Python path: {python_executable}")
        
        # 检查关键模块
        required_modules = ['flask', 'cryptography', 'numpy']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"[+] Module {module} is installed")
            except ImportError:
                missing_modules.append(module)
                print(f"[-] Module {module} is NOT installed")
        
        if missing_modules:
            print(f"\n[!] Missing modules: {', '.join(missing_modules)}")
            print("[!] Please run: pip install -r requirements.txt")
            return False
        
        return True
        
    except Exception as e:
        print(f"[-] Python environment check failed: {e}")
        return False

def check_system():
    """检查系统环境"""
    print("\n[-] Checking system environment...")
    
    system_info = {
        'System': platform.system(),
        'Version': platform.version(),
        'Architecture': platform.architecture()[0],
        'Processor': platform.processor(),
        'Python build': platform.python_build()
    }
    
    for key, value in system_info.items():
        print(f"[+] {key}: {value}")
    
    return True

def check_project_structure():
    """检查项目结构"""
    print("\n[-] Checking project structure...")
    
    required_dirs = [
        'server',
        'client', 
        'config',
        'cost_optimizer',
        'logs',
        'data'
    ]
    
    required_files = [
        'requirements.txt',
        'Dockerfile',
        'docker-compose.yml',
        'server/main.py',
        'client/main.py'
    ]
    
    missing_dirs = []
    missing_files = []
    
    # 检查目录
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"[+] Directory {dir_path}/ exists")
        else:
            missing_dirs.append(dir_path)
            print(f"[-] Directory {dir_path}/ NOT exists")
    
    # 检查文件
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"[+] File {file_path} exists")
        else:
            missing_files.append(file_path)
            print(f"[-] File {file_path} NOT exists")
    
    if missing_dirs or missing_files:
        print("\n[!] Project structure is incomplete")
        if missing_dirs:
            print(f"[!] Need to create directories: {', '.join(missing_dirs)}")
        if missing_files:
            print(f"[!] Need to create files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("      Smart Secure Email System - Environment Check")
    print("=" * 60)
    print()
    
    checks_passed = 0
    total_checks = 3
    
    # 检查系统
    if check_system():
        checks_passed += 1
    
    # 检查Python
    python_ok = check_python()
    if python_ok:
        checks_passed += 1
    
    # 检查项目结构
    structure_ok = check_project_structure()
    if structure_ok:
        checks_passed += 1
    
    print(f"\n[+] Check results: {checks_passed}/{total_checks} items passed")
    
    if checks_passed == total_checks:
        print("\n[!] All checks passed! System is ready to run")
        print("\n[+] Start suggestions:")
        print("  Option 1: Docker start - docker-compose up -d")
        print("  Option 2: Python start - python start_servers.py")
        print("  Option 3: Demo mode - python cost_optimizer/demo_system.py")
    else:
        print("\n[!] Environment incomplete, suggestions:")
        
        if not python_ok:
            print("  1. Install Python 3.8+")
            print("  2. Install pip")
            print("  3. Run: pip install -r requirements.txt")
    
    print("\n" + "=" * 60)
    print("      Environment check completed")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[+] User interrupted")
    except Exception as e:
        print(f"\n[-] Error during check: {e}")
