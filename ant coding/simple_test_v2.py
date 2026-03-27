#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版测试脚本 - 验证服务器功能
"""

import sys
import socket
import time
import json
from pathlib import Path

def check_server_status(host='localhost', port=8080, timeout=2):
    """检查服务器状态"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"[-] Error checking server: {e}")
        return False

def test_server_connection():
    """测试服务器连接"""
    print("=" * 60)
    print("Server Connection Test")
    print("=" * 60)
    print()
    
    servers = [
        ("Domain 1", "localhost", 8080),
        ("Domain 2", "localhost", 8081)
    ]
    
    all_passed = True
    
    for name, host, port in servers:
        print(f"Testing {name} ({host}:{port})...")
        
        if check_server_status(host, port):
            print(f"  [+] Server is running")
        else:
            print(f"  [-] Server is not responding")
            all_passed = False
        
        time.sleep(0.5)
    
    print()
    return all_passed

def test_project_structure():
    """测试项目结构"""
    print("=" * 60)
    print("Project Structure Test")
    print("=" * 60)
    print()
    
    required_items = [
        ("server/main.py", "file"),
        ("server/server_manager.py", "file"),
        ("server/mail_handler.py", "file"),
        ("server/security.py", "file"),
        ("server/storage_manager.py", "file"),
        ("server/protocols.py", "file"),
        ("client/main.py", "file"),
        ("client/client_ui.py", "file"),
        ("config/domain1_config.json", "file"),
        ("config/domain2_config.json", "file"),
        ("config/security_config.json", "file"),
        ("cost_optimizer/dynamic_cost_engine.py", "file"),
        ("requirements.txt", "file"),
        ("data/", "dir"),
        ("logs/", "dir")
    ]
    
    all_passed = True
    
    for item_path, item_type in required_items:
        path = Path(item_path)
        
        if item_type == "file":
            exists = path.is_file()
        else:
            exists = path.is_dir()
        
        status = "[+]" if exists else "[-]"
        item_type_text = "File" if item_type == "file" else "Directory"
        
        print(f"{status} {item_type_text}: {item_path}")
        
        if not exists:
            all_passed = False
    
    print()
    return all_passed

def test_python_modules():
    """测试Python模块导入"""
    print("=" * 60)
    print("Python Modules Test")
    print("=" * 60)
    print()
    
    modules = [
        'socket',
        'json',
        'threading',
        'logging',
        'pathlib',
        'cryptography',
        'flask',
        'numpy'
    ]
    
    all_passed = True
    
    for module in modules:
        try:
            __import__(module)
            print(f"[+] Module {module} is available")
        except ImportError:
            print(f"[-] Module {module} is NOT available")
            all_passed = False
    
    print()
    return all_passed

def test_config_files():
    """测试配置文件"""
    print("=" * 60)
    print("Configuration Files Test")
    print("=" * 60)
    print()
    
    config_files = [
        "config/domain1_config.json",
        "config/domain2_config.json",
        "config/security_config.json"
    ]
    
    all_passed = True
    
    for config_file in config_files:
        print(f"Checking {config_file}...")
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"  [+] File exists and is valid JSON")
            print(f"  [+] Keys: {', '.join(list(config.keys())[:5])}...")
            
        except FileNotFoundError:
            print(f"  [-] File not found")
            all_passed = False
        except json.JSONDecodeError as e:
            print(f"  [-] Invalid JSON: {e}")
            all_passed = False
        except Exception as e:
            print(f"  [-] Error: {e}")
            all_passed = False
        
        print()
    
    return all_passed

def main():
    """主函数"""
    print("\n")
    print("*" * 60)
    print("*" + " " * 58 + "*")
    print("*" + "  Smart Secure Email System - Quick Test  ".center(58) + "*")
    print("*" + " " * 58 + "*")
    print("*" * 60)
    print()
    
    tests = [
        ("Python Modules", test_python_modules),
        ("Project Structure", test_project_structure),
        ("Configuration Files", test_config_files),
        ("Server Connection", test_server_connection)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"[-] Error in {test_name}: {e}")
            results[test_name] = False
            print()
    
    # 显示汇总结果
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    
    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print()
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n[+] All tests passed! System is ready.")
        print("[+] You can now:")
        print("    1. Use the web interface: http://localhost:8080")
        print("    2. Run the client: python client/main.py")
        print("    3. View cost optimization demo: python cost_optimizer/demo_system.py")
        return 0
    else:
        print(f"\n[-] {total_tests - passed_tests} test(s) failed.")
        print("[-] Please check the errors above and fix them.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[!] Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[-] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
