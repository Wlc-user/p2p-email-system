#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试安全模块导入
"""

import os
import sys

print("测试安全模块导入...")
print("当前工作目录:", os.getcwd())
print("Python路径:", sys.path)

try:
    # 尝试导入安全模块
    from server.security import SecurityManager, generate_secure_password
    print("✓ 成功导入SecurityManager")
    print("✓ 成功导入generate_secure_password")
    
    # 测试基本功能
    config = {
        'encryption_key': 'test_key',
        'jwt_secret': 'test_secret'
    }
    
    security = SecurityManager(config)
    print("✓ 成功创建SecurityManager实例")
    
    # 测试密码生成
    password = generate_secure_password(12)
    print(f"✓ 成功生成密码: {password}")
    
    # 测试密码哈希
    hashed = security.hash_password(password)
    print(f"✓ 成功哈希密码")
    
    # 测试密码验证
    verified = security.verify_password(password, hashed)
    print(f"✓ 密码验证: {'成功' if verified else '失败'}")
    
    security.cleanup()
    print("✓ 成功清理安全管理器")
    
    print("\n所有导入测试通过！")
    
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"✗ 其他错误: {e}")
    import traceback
    traceback.print_exc()