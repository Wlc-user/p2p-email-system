#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试 - 验证双域名邮箱系统的核心功能
"""

import os
import sys
import time
import threading
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

def test_basic_functionality():
    """测试基本功能"""
    
    print("=" * 60)
    print("快速测试 - 智能安全邮箱系统")
    print("=" * 60)
    
    # 1. 测试模块导入
    print("\n1. 测试模块导入...")
    try:
        from server.protocols import Message, MessageType, Mail, MailAddress, MailStatus
        from server.storage_manager import StorageManager
        from server.security import SecurityManager
        from server.mail_handler import MailHandler
        from server.server_manager import ServerManager
        from client.main import MailClient
        
        print("[+] All modules imported successfully")
    except ImportError as e:
        print(f"[-] Module import failed: {e}")
        return False
    
    # 2. 测试协议定义
    print("\n2. 测试协议定义...")
    try:
        # 测试邮件地址
        address = MailAddress.from_string("user@example.com")
        assert address.username == "user"
        assert address.domain == "example.com"
        assert address.full_address == "user@example.com"
        
        # 测试消息创建
        message = Message.create(MessageType.PING, {})
        json_str = message.to_json()
        message2 = Message.from_json(json_str)
        assert message2.message_type == MessageType.PING
        
        print("[+] Protocol definition test passed")
    except Exception as e:
        print(f"✗ 协议定义测试失败: {e}")
        return False
    
    # 3. 测试存储管理器
    print("\n3. 测试存储管理器...")
    try:
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        storage_manager = StorageManager(temp_dir)
        
        # 测试用户创建
        user_data = storage_manager.create_user(
            username="testuser",
            domain="test.com",
            password="testpass",
            email="test@test.com"
        )
        
        assert user_data is not None
        assert user_data["username"] == "testuser"
        
        # 测试用户验证
        auth_user = storage_manager.authenticate_user(
            username="testuser",
            domain="test.com",
            password="testpass"
        )
        
        assert auth_user is not None
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir)
        
        print("✓ 存储管理器测试通过")
    except Exception as e:
        print(f"✗ 存储管理器测试失败: {e}")
        return False
    
    # 4. 测试安全管理器
    print("\n4. 测试安全管理器...")
    try:
        config = {
            'encryption_key': 'test-key-1234567890',
            'jwt_secret': 'test-secret-1234567890',
            'salt_length': 16
        }
        
        security_manager = SecurityManager(config)
        
        # 测试密码哈希
        password = "TestPass123!"
        hashed = security_manager.hash_password(password)
        verified = security_manager.verify_password(password, hashed)
        assert verified == True
        
        # 测试密码强度验证
        is_strong, message = security_manager.validate_password_strength(password)
        assert is_strong == True
        
        # 测试令牌管理
        token = security_manager.generate_token("testuser", "test.com")
        assert security_manager.verify_token(token) == True
        
        print("[+] Security manager test passed")
    except Exception as e:
        print(f"[-] Security manager test failed: {e}")
        return False
    
    # 5. 测试客户端创建
    print("\n5. 测试客户端创建...")
    try:
        client = MailClient("127.0.0.1", 8080)
        
        # 检查客户端配置
        assert client.config is not None
        assert "servers" in client.config
        
        print("[+] Client creation test passed")
    except Exception as e:
        print(f"[-] Client creation test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[+] All basic tests passed!")
    print("=" * 60)
    print("\n系统包含以下组件:")
    print("  1. 协议定义 (protocols.py)")
    print("  2. 存储管理器 (storage_manager.py)")
    print("  3. 安全管理器 (security.py)")
    print("  4. 邮件处理器 (mail_handler.py)")
    print("  5. 服务器管理器 (server_manager.py)")
    print("  6. 客户端 (client/)")
    print("  7. 配置文件 (config/)")
    print("\n可以运行完整集成测试:")
    print("  python integration_test.py")
    
    return True

def check_config_files():
    """检查配置文件"""
    
    print("\n" + "=" * 60)
    print("检查配置文件...")
    print("=" * 60)
    
    config_files = [
        ("config/domain1_config.json", True),
        ("config/domain2_config.json", True),
        ("config/security_config.json", True),
        ("server/main.py", True),
        ("server/server_manager.py", True),
        ("server/mail_handler.py", True),
        ("server/storage_manager.py", True),
        ("server/security.py", True),
        ("server/protocols.py", True),
        ("client/main.py", True),
        ("client/client_ui.py", True)
    ]
    
    all_exists = True
    for file_path, required in config_files:
        exists = os.path.exists(file_path)
        status = "[+]" if exists else "[-]"
        
        if required and not exists:
            all_exists = False
            print(f"{status} {file_path} - {'EXISTS' if exists else 'MISSING'}")
        else:
            print(f"{status} {file_path} - {'EXISTS' if exists else 'OPTIONAL'}")
    
    return all_exists

def main():
    """主函数"""
    
    print("智能安全邮箱系统 - 快速功能验证")
    print("=" * 60)
    
    # 检查配置文件
    if not check_config_files():
        print("\n⚠️  部分配置文件缺失，可能影响功能测试")
        response = input("是否继续测试? (y/n): ")
        if response.lower() != 'y':
            return
    
    # 运行基础功能测试
    success = test_basic_functionality()
    
    if success:
        print("\n[!] System core functionality verified!")
        print("\nNext steps:")
        print("  1. Run full integration test: python integration_test.py")
        print("  2. Start dual servers: python server/main.py")
        print("  3. Run client: python client/main.py")
    else:
        print("\n[!] Basic functionality tests failed, please check implementation")
    
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试出现异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)