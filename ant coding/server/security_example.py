#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全模块使用示例
"""

import os
import sys
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 导入安全模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from server.security import SecurityManager, generate_secure_password, sanitize_input


def example_password_security():
    """密码安全示例"""
    print("=" * 60)
    print("密码安全示例")
    print("=" * 60)
    
    # 创建安全配置
    config = {
        'encryption_key': 'your_secure_encryption_key_here',
        'jwt_secret': 'your_secure_jwt_secret_here',
        'salt_length': 32
    }
    
    security = SecurityManager(config)
    
    # 1. 生成安全密码
    secure_pass = generate_secure_password(16)
    print(f"1. 生成的安全密码: {secure_pass}")
    
    # 2. 哈希密码
    hashed_password = security.hash_password(secure_pass)
    print(f"2. 哈希后的密码: {hashed_password[:50]}...")
    
    # 3. 验证密码
    is_valid = security.verify_password(secure_pass, hashed_password)
    print(f"3. 密码验证结果: {'成功' if is_valid else '失败'}")
    
    # 4. 密码强度检查
    test_passwords = [
        "weak",           # 太弱
        "weak123",        # 缺少大写和特殊字符
        "Weak123",        # 缺少特殊字符
        "Weak@123",       # 强密码
    ]
    
    for pwd in test_passwords:
        is_strong, message = security.validate_password_strength(pwd)
        strength = "强" if is_strong else "弱"
        print(f"   密码 '{pwd}': {strength} - {message}")
    
    security.cleanup()
    print()


def example_login_security():
    """登录安全示例"""
    print("=" * 60)
    print("登录安全示例")
    print("=" * 60)
    
    config = {
        'encryption_key': 'test_key',
        'jwt_secret': 'test_secret',
        'max_login_attempts': 3,
        'login_lockout_minutes': 1
    }
    
    security = SecurityManager(config)
    
    username = "alice"
    client_ip = "192.168.1.100"
    
    print(f"用户: {username}, IP: {client_ip}")
    
    # 模拟登录尝试
    attempts = [
        (False, "密码错误"),
        (False, "密码错误"),
        (False, "密码错误"),
        (False, "账户已锁定")
    ]
    
    for i, (success, desc) in enumerate(attempts, 1):
        if security.is_login_blocked(username, client_ip):
            print(f"  尝试 {i}: 账户已被锁定")
            break
        
        security.record_login_attempt(username, client_ip, success)
        print(f"  尝试 {i}: {desc}")
    
    # 等待锁定解除
    import time
    print("  等待70秒锁定解除...")
    time.sleep(70)
    
    # 再次尝试
    if not security.is_login_blocked(username, client_ip):
        security.record_login_attempt(username, client_ip, True)
        print("  成功登录！")
    
    security.cleanup()
    print()


def example_email_security():
    """邮件安全示例"""
    print("=" * 60)
    print("邮件安全示例")
    print("=" * 60)
    
    config = {
        'encryption_key': 'test_key',
        'jwt_secret': 'test_secret',
        'phishing_patterns': ['紧急', '密码', '账户', '验证'],
        'spam_keywords': ['促销', '免费', '获奖', '幸运']
    }
    
    security = SecurityManager(config)
    
    # 测试邮件内容
    test_emails = [
        {
            "subject": "会议通知",
            "body": "您好，本周五下午2点有团队会议，请准时参加。",
            "type": "正常邮件"
        },
        {
            "subject": "紧急！您的账户需要验证",
            "body": "请立即点击链接验证您的账户：http://example.com/verify",
            "type": "钓鱼邮件"
        },
        {
            "subject": "恭喜您获奖！",
            "body": "您是我们第10000位用户，获得免费iPhone一部！立即领取：http://spam.com",
            "type": "垃圾邮件"
        }
    ]
    
    for email in test_emails:
        is_spam, score, reasons = security.check_spam_content(
            email["subject"], email["body"]
        )
        
        spam_status = "垃圾邮件" if is_spam else "正常邮件"
        print(f"  {email['type']}: {spam_status} (得分: {score:.2f})")
        if reasons:
            print(f"    原因: {', '.join(reasons[:2])}")
    
    # 测试附件安全
    print("\n附件安全测试:")
    test_files = [
        ("document.pdf", 5 * 1024 * 1024),      # 5MB PDF - 应该通过
        ("script.exe", 1 * 1024 * 1024),        # 1MB EXE - 应该被阻止
        ("large_video.mp4", 50 * 1024 * 1024),  # 50MB MP4 - 超过大小限制
        ("../../passwd.txt", 100 * 1024),       # 恶意文件名
    ]
    
    for filename, size in test_files:
        is_valid, message = security.validate_attachment(filename, size)
        status = "通过" if is_valid else "拒绝"
        print(f"  {filename} ({size//1024}KB): {status} - {message}")
    
    security.cleanup()
    print()


def example_encryption():
    """加密示例"""
    print("=" * 60)
    print("数据加密示例")
    print("=" * 60)
    
    config = {
        'encryption_key': 'test_encryption_key_32_bytes_long_enough',
        'jwt_secret': 'test_jwt_secret_32_bytes_long_enough'
    }
    
    security = SecurityManager(config)
    
    # 敏感数据
    sensitive_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecretPass123!",
        "credit_card": "4111-1111-1111-1111"
    }
    
    print("原始数据:")
    print(json.dumps(sensitive_data, indent=2, ensure_ascii=False))
    
    # 加密存储
    encrypted = security.encrypt_for_storage(sensitive_data)
    print(f"\n加密后数据 (前100字符):")
    print(encrypted[:100] + "...")
    
    # 解密
    decrypted = security.decrypt_from_storage(encrypted)
    print("\n解密后数据:")
    print(json.dumps(decrypted, indent=2, ensure_ascii=False))
    
    # 验证数据完整性
    if decrypted == sensitive_data:
        print("✓ 加密/解密成功，数据完整")
    else:
        print("✗ 加密/解密失败，数据损坏")
    
    security.cleanup()
    print()


def example_input_sanitization():
    """输入清理示例"""
    print("=" * 60)
    print("输入清理示例")
    print("=" * 60)
    
    # 测试各种输入
    test_inputs = [
        ("正常输入", "Hello World!"),
        ("XSS攻击", "<script>alert('XSS')</script>"),
        ("SQL注入", "SELECT * FROM users WHERE 1=1"),
        ("路径遍历", "../../../etc/passwd"),
        ("命令注入", "; rm -rf /"),
        ("超长输入", "A" * 2000)
    ]
    
    for name, input_str in test_inputs:
        sanitized = sanitize_input(input_str)
        original_len = len(input_str)
        sanitized_len = len(sanitized)
        
        print(f"  {name}:")
        print(f"    原始: {input_str[:50]}{'...' if original_len > 50 else ''}")
        print(f"    清理后: {sanitized[:50]}{'...' if sanitized_len > 50 else ''}")
        print(f"    长度: {original_len} → {sanitized_len}")
        print()


def example_security_monitoring():
    """安全监控示例"""
    print("=" * 60)
    print("安全监控示例")
    print("=" * 60)
    
    config = {
        'encryption_key': 'test_key',
        'jwt_secret': 'test_secret',
        'audit_log_enabled': True,
        'audit_db_path': 'example_audit.db'
    }
    
    security = SecurityManager(config)
    
    # 模拟安全事件
    events = [
        {
            "type": "USER_LOGIN",
            "severity": "INFO",
            "username": "alice",
            "ip": "192.168.1.100",
            "details": {"status": "success", "method": "password"}
        },
        {
            "type": "FAILED_LOGIN",
            "severity": "WARNING",
            "username": "bob",
            "ip": "192.168.1.200",
            "details": {"attempts": 3, "reason": "wrong_password"}
        },
        {
            "type": "SUSPICIOUS_ACTIVITY",
            "severity": "ERROR",
            "username": "charlie",
            "ip": "10.0.0.50",
            "details": {"action": "multiple_failed_logins", "count": 10}
        }
    ]
    
    for event in events:
        security.log_security_event(
            event["type"],
            event["details"],
            severity=event["severity"],
            username=event["username"],
            ip_address=event["ip"]
        )
        print(f"  记录事件: {event['type']} - {event['severity']}")
    
    # 查询审计日志
    print("\n查询最近的安全事件:")
    recent_events = security.get_audit_events(limit=5)
    
    for event in recent_events:
        print(f"  [{event['timestamp']}] {event['event_type']} - {event['severity']}")
        if event.get('username'):
            print(f"    用户: {event['username']}, IP: {event.get('ip_address', 'N/A')}")
    
    security.cleanup()
    
    # 清理临时文件
    if os.path.exists('example_audit.db'):
        os.remove('example_audit.db')
    
    print()


def main():
    """主函数"""
    print("智能安全邮箱系统 - 安全模块演示")
    print("=" * 60)
    
    # 运行所有示例
    example_password_security()
    example_login_security()
    example_email_security()
    example_encryption()
    example_input_sanitization()
    example_security_monitoring()
    
    print("=" * 60)
    print("安全模块演示完成")
    print("=" * 60)
    
    # 提示用户
    print("\n使用建议:")
    print("1. 在生产环境中，请使用强加密密钥")
    print("2. 定期更换加密密钥和JWT密钥")
    print("3. 启用审计日志并定期检查")
    print("4. 根据业务需求调整安全策略")
    print("5. 定期进行安全测试和漏洞扫描")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示出错: {e}")
        import traceback
        traceback.print_exc()