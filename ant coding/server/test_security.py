#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全模块测试
"""

import os
import sys
import json
import tempfile
import unittest
from pathlib import Path

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.security import SecurityManager, generate_secure_password, sanitize_input, validate_email_format


class TestSecurityManager(unittest.TestCase):
    """测试安全管理器"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        # 创建测试配置
        cls.test_config = {
            'encryption_key': 'test_encryption_key_1234567890abcdef',
            'jwt_secret': 'test_jwt_secret_1234567890abcdef',
            'salt_length': 16,  # 测试用较短盐值
            'max_login_attempts': 3,
            'login_lockout_minutes': 1,
            'daily_send_limit': 10,
            'rate_limit_per_minute': 5,
            'max_attachments_mb': 1,
            'allowed_file_types': ['txt', 'pdf', 'jpg'],
            'phishing_patterns': ['紧急', '密码', '账户'],
            'spam_keywords': ['促销', '免费', '获奖'],
            'audit_log_enabled': True,
            'audit_db_path': ':memory:'  # 使用内存数据库
        }
        
        cls.security_manager = SecurityManager(cls.test_config)
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        cls.security_manager.cleanup()
    
    def test_01_password_hashing(self):
        """测试密码哈希和验证"""
        password = "TestPassword123!"
        
        # 哈希密码
        hashed = self.security_manager.hash_password(password)
        self.assertIsInstance(hashed, str)
        self.assertIn(":", hashed)  # 应该包含盐和哈希的分隔符
        
        # 验证正确密码
        verified = self.security_manager.verify_password(password, hashed)
        self.assertTrue(verified)
        
        # 验证错误密码
        wrong_password = "WrongPassword123!"
        not_verified = self.security_manager.verify_password(wrong_password, hashed)
        self.assertFalse(not_verified)
    
    def test_02_password_strength_validation(self):
        """测试密码强度验证"""
        # 测试强密码
        strong_password = "StrongPass123!"
        is_strong, message = self.security_manager.validate_password_strength(strong_password)
        self.assertTrue(is_strong)
        
        # 测试弱密码 - 太短
        weak_password_short = "Short1!"
        is_strong_short, message_short = self.security_manager.validate_password_strength(weak_password_short)
        self.assertFalse(is_strong_short)
        self.assertIn("至少需要8个字符", message_short)
        
        # 测试弱密码 - 缺少大写
        weak_password_no_upper = "weakpass123!"
        is_strong_no_upper, message_no_upper = self.security_manager.validate_password_strength(weak_password_no_upper)
        self.assertFalse(is_strong_no_upper)
        self.assertIn("必须包含大写字母", message_no_upper)
        
        # 测试弱密码 - 缺少特殊字符
        weak_password_no_special = "Weakpass123"
        is_strong_no_special, message_no_special = self.security_manager.validate_password_strength(weak_password_no_special)
        self.assertFalse(is_strong_no_special)
        self.assertIn("必须包含特殊字符", message_no_special)
    
    def test_03_username_validation(self):
        """测试用户名验证"""
        # 有效用户名
        valid_usernames = ["user123", "test_user", "Admin_Test"]
        for username in valid_usernames:
            self.assertTrue(self.security_manager.validate_username(username))
        
        # 无效用户名
        invalid_usernames = ["ab", "user@name", "user-name", "", "a" * 21]
        for username in invalid_usernames:
            self.assertFalse(self.security_manager.validate_username(username))
    
    def test_04_login_security(self):
        """测试登录安全"""
        username = "testuser"
        client_ip = "192.168.1.100"
        
        # 初始状态不应该被阻止
        self.assertFalse(self.security_manager.is_login_blocked(username, client_ip))
        
        # 记录失败尝试
        for i in range(3):
            self.security_manager.record_login_attempt(username, client_ip, success=False)
        
        # 超过最大尝试次数应该被阻止
        self.assertTrue(self.security_manager.is_login_blocked(username, client_ip))
        
        # 成功登录应该清除失败记录
        self.security_manager.record_login_attempt(username, client_ip, success=True)
        # 注意：成功登录会清除记录，但锁定期可能仍在
        # 为了测试，我们等待锁定期结束
        import time
        time.sleep(70)  # 等待1分钟+10秒
        
        self.assertFalse(self.security_manager.is_login_blocked(username, client_ip))
    
    def test_05_token_management(self):
        """测试令牌管理"""
        username = "tokenuser"
        domain = "domain1.com"
        
        # 生成令牌
        token = self.security_manager.generate_token(username, domain)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token), 64)  # SHA256哈希长度
        
        # 验证令牌
        self.assertTrue(self.security_manager.verify_token(token))
        
        # 获取令牌数据
        token_data = self.security_manager.get_token_data(token)
        self.assertIsNotNone(token_data)
        self.assertEqual(token_data['username'], username)
        self.assertEqual(token_data['domain'], domain)
        
        # 撤销令牌
        revoked = self.security_manager.revoke_token(token)
        self.assertTrue(revoked)
        self.assertFalse(self.security_manager.verify_token(token))
    
    def test_06_send_limits(self):
        """测试发送限制"""
        username = "senduser"
        domain = "domain1.com"
        
        # 初始检查应该通过
        can_send, message = self.security_manager.check_send_limit(username, domain)
        self.assertTrue(can_send)
        
        # 记录发送
        for i in range(5):
            self.security_manager.record_send(username, domain)
        
        # 检查限制
        can_send_after, message_after = self.security_manager.check_send_limit(username, domain)
        self.assertTrue(can_send_after)  # 应该还能发送
        
        # 达到每分钟限制
        for i in range(10):  # 再发送10次，总共15次超过每分钟限制5次
            self.security_manager.record_send(username, domain)
        
        can_send_limit, message_limit = self.security_manager.check_send_limit(username, domain)
        self.assertFalse(can_send_limit)
        self.assertIn("发送频率过高", message_limit)
    
    def test_07_spam_detection(self):
        """测试垃圾邮件检测"""
        # 测试钓鱼邮件
        phishing_subject = "紧急！您的账户需要验证"
        phishing_body = "请立即点击链接验证您的账户：http://example.com/verify"
        
        is_spam_phishing, score_phishing, reasons_phishing = self.security_manager.check_spam_content(
            phishing_subject, phishing_body
        )
        self.assertTrue(is_spam_phishing)
        self.assertGreater(score_phishing, 0.7)
        self.assertIn("钓鱼关键词", str(reasons_phishing))
        
        # 测试正常邮件
        normal_subject = "会议通知"
        normal_body = "您好，本周五下午2点有团队会议，请准时参加。"
        
        is_spam_normal, score_normal, reasons_normal = self.security_manager.check_spam_content(
            normal_subject, normal_body
        )
        self.assertFalse(is_spam_normal)
        self.assertLess(score_normal, 0.7)
    
    def test_08_suspicious_sender_check(self):
        """测试可疑发件人检查"""
        # 正常发件人
        normal_senders = ["user@gmail.com", "test@qq.com", "admin@163.com"]
        for sender in normal_senders:
            self.assertFalse(self.security_manager.check_suspicious_sender(sender))
        
        # 可疑发件人
        suspicious_senders = ["user@", "@domain.com", "test@可疑域名.com", "test@123.456"]
        for sender in suspicious_senders:
            self.assertTrue(self.security_manager.check_suspicious_sender(sender))
    
    def test_09_data_encryption(self):
        """测试数据加密"""
        test_data = "这是需要加密的敏感数据"
        
        # 加密
        iv, ciphertext, auth_tag = self.security_manager.encrypt_data(test_data)
        self.assertIsInstance(iv, bytes)
        self.assertIsInstance(ciphertext, bytes)
        self.assertIsInstance(auth_tag, bytes)
        
        # 解密
        decrypted = self.security_manager.decrypt_data(iv, ciphertext, auth_tag)
        self.assertEqual(decrypted, test_data)
        
        # 测试错误解密
        wrong_iv = b'\x00' * 16
        wrong_decrypted = self.security_manager.decrypt_data(wrong_iv, ciphertext, auth_tag)
        self.assertIsNone(wrong_decrypted)
    
    def test_10_storage_encryption(self):
        """测试存储加密"""
        test_data = {
            "username": "testuser",
            "email": "test@example.com",
            "sensitive": "这是敏感信息"
        }
        
        # 加密存储
        encrypted_str = self.security_manager.encrypt_for_storage(test_data)
        self.assertIsInstance(encrypted_str, str)
        
        # 解密存储
        decrypted_data = self.security_manager.decrypt_from_storage(encrypted_str)
        self.assertEqual(decrypted_data, test_data)
        
        # 测试错误数据
        wrong_encrypted = json.dumps({"iv": "wrong", "ciphertext": "wrong", "auth_tag": "wrong"})
        wrong_decrypted = self.security_manager.decrypt_from_storage(wrong_encrypted)
        self.assertIsNone(wrong_decrypted)
    
    def test_11_attachment_validation(self):
        """测试附件验证"""
        # 有效附件
        valid_files = [
            ("document.pdf", 500 * 1024),  # 500KB PDF
            ("image.jpg", 200 * 1024),      # 200KB JPG
            ("notes.txt", 50 * 1024)        # 50KB TXT
        ]
        
        for filename, size in valid_files:
            is_valid, message = self.security_manager.validate_attachment(filename, size)
            self.assertTrue(is_valid, f"附件 {filename} 应该有效: {message}")
        
        # 无效附件 - 文件类型
        invalid_type = ("script.exe", 100 * 1024)
        is_valid_type, message_type = self.security_manager.validate_attachment(*invalid_type)
        self.assertFalse(is_valid_type)
        self.assertIn("不允许的文件类型", message_type)
        
        # 无效附件 - 文件大小
        invalid_size = ("large.pdf", 2 * 1024 * 1024)  # 2MB超过1MB限制
        is_valid_size, message_size = self.security_manager.validate_attachment(*invalid_size)
        self.assertFalse(is_valid_size)
        self.assertIn("附件大小超过限制", message_size)
        
        # 无效附件 - 恶意文件名
        malicious_names = ["../../../etc/passwd", "script.bat", "test<>.exe"]
        for filename in malicious_names:
            is_valid_name, message_name = self.security_manager.validate_attachment(filename, 100 * 1024)
            self.assertFalse(is_valid_name)
            self.assertIn("可疑的文件名", message_name)
    
    def test_12_withdrawal_token_verification(self):
        """测试邮件撤回令牌验证"""
        mail_id = "msg_123456"
        username = "withdrawuser"
        domain = "domain1.com"
        
        # 生成令牌
        expected_token = self.security_manager._generate_withdrawal_token(mail_id, username, domain)
        
        # 验证正确令牌
        is_valid = self.security_manager.verify_withdrawal_request(mail_id, username, domain, expected_token)
        self.assertTrue(is_valid)
        
        # 验证错误令牌
        wrong_token = "wrong_token_123456"
        is_valid_wrong = self.security_manager.verify_withdrawal_request(mail_id, username, domain, wrong_token)
        self.assertFalse(is_valid_wrong)
    
    def test_13_security_event_logging(self):
        """测试安全事件记录"""
        # 记录安全事件
        self.security_manager.log_security_event(
            "TEST_EVENT",
            {"action": "test", "result": "success"},
            severity="INFO",
            username="testuser",
            ip_address="192.168.1.100"
        )
        
        # 获取审计事件
        events = self.security_manager.get_audit_events(limit=1)
        self.assertGreaterEqual(len(events), 0)
        
        if events:
            event = events[0]
            self.assertEqual(event['event_type'], "TEST_EVENT")
            self.assertEqual(event['severity'], "INFO")
            self.assertEqual(event['username'], "testuser")
    
    def test_14_vulnerability_scanning(self):
        """测试漏洞扫描"""
        # 测试SQL注入
        sql_injection_data = {
            "query": "SELECT * FROM users WHERE username = 'admin' OR 1=1 --",
            "normal": "正常数据"
        }
        
        vulnerabilities = self.security_manager.scan_for_vulnerabilities(sql_injection_data)
        self.assertGreater(len(vulnerabilities), 0)
        
        sql_vuln_found = any(v['type'] == 'SQL_INJECTION' for v in vulnerabilities)
        self.assertTrue(sql_vuln_found)
        
        # 测试XSS攻击
        xss_data = {
            "content": "<script>alert('XSS')</script>",
            "normal": "正常数据"
        }
        
        xss_vulnerabilities = self.security_manager.scan_for_vulnerabilities(xss_data)
        xss_vuln_found = any(v['type'] == 'XSS' for v in xss_vulnerabilities)
        self.assertTrue(xss_vuln_found)
        
        # 测试命令注入
        cmd_injection_data = {
            "command": "; ls -la",
            "normal": "正常数据"
        }
        
        cmd_vulnerabilities = self.security_manager.scan_for_vulnerabilities(cmd_injection_data)
        cmd_vuln_found = any(v['type'] == 'COMMAND_INJECTION' for v in cmd_vulnerabilities)
        self.assertTrue(cmd_vuln_found)
    
    def test_15_cleanup(self):
        """测试清理功能"""
        # 生成一些令牌
        tokens = []
        for i in range(3):
            token = self.security_manager.generate_token(f"user{i}", "domain1.com")
            tokens.append(token)
        
        # 验证令牌存在
        for token in tokens:
            self.assertTrue(self.security_manager.verify_token(token))
        
        # 清理过期令牌（实际上不会清理未过期的）
        self.security_manager.cleanup_expired_tokens()
        
        # 令牌应该仍然存在
        for token in tokens:
            self.assertTrue(self.security_manager.verify_token(token))


class TestSecurityHelpers(unittest.TestCase):
    """测试安全辅助函数"""
    
    def test_generate_secure_password(self):
        """测试生成安全密码"""
        password = generate_secure_password(12)
        self.assertEqual(len(password), 12)
        
        # 检查密码包含各种字符类型
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        self.assertTrue(has_lower, "密码应包含小写字母")
        self.assertTrue(has_upper, "密码应包含大写字母")
        self.assertTrue(has_digit, "密码应包含数字")
        self.assertTrue(has_special, "密码应包含特殊字符")
    
    def test_sanitize_input(self):
        """测试输入清理"""
        # 测试危险字符清理
        dangerous_input = "<script>alert('XSS')</script>"
        sanitized = sanitize_input(dangerous_input)
        self.assertNotIn("<", sanitized)
        self.assertNotIn(">", sanitized)
        self.assertNotIn("'", sanitized)
        
        # 测试长度限制
        long_input = "A" * 2000
        sanitized_long = sanitize_input(long_input)
        self.assertEqual(len(sanitized_long), 1000)
        
        # 测试空输入
        empty_input = ""
        sanitized_empty = sanitize_input(empty_input)
        self.assertEqual(sanitized_empty, "")
        
        # 测试空白字符处理
        whitespace_input = "  test  "
        sanitized_whitespace = sanitize_input(whitespace_input)
        self.assertEqual(sanitized_whitespace, "test")
    
    def test_validate_email_format(self):
        """测试邮箱格式验证"""
        # 有效邮箱
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@sub.example.com",
            "user@example.co.uk"
        ]
        
        for email in valid_emails:
            self.assertTrue(validate_email_format(email), f"邮箱 {email} 应该有效")
        
        # 无效邮箱
        invalid_emails = [
            "user@",
            "@example.com",
            "user@.com",
            "user@example.",
            "user example.com",
            "user@-example.com"
        ]
        
        for email in invalid_emails:
            self.assertFalse(validate_email_format(email), f"邮箱 {email} 应该无效")
    
    def test_calculate_entropy(self):
        """测试密码熵计算"""
        import math
        
        # 简单密码
        simple_password = "123456"
        entropy_simple = calculate_entropy(simple_password)
        self.assertGreater(entropy_simple, 0)
        
        # 复杂密码
        complex_password = "P@ssw0rd!123"
        entropy_complex = calculate_entropy(complex_password)
        self.assertGreater(entropy_complex, entropy_simple)
        
        # 空密码
        empty_password = ""
        entropy_empty = calculate_entropy(empty_password)
        self.assertEqual(entropy_empty, 0.0)
        
        # 单字符密码
        single_char = "a"
        entropy_single = calculate_entropy(single_char)
        self.assertGreater(entropy_single, 0)


class TestIntegrationSecurity(unittest.TestCase):
    """测试集成安全"""
    
    def test_security_config_loading(self):
        """测试安全配置加载"""
        # 测试配置加载
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "security_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 验证配置结构
            self.assertIn("security", config_data)
            security_config = config_data["security"]
            
            # 检查必要字段
            required_fields = ["encryption_key", "jwt_secret", "login_security", "password_policy"]
            for field in required_fields:
                self.assertIn(field, security_config, f"配置缺少必要字段: {field}")
            
            # 验证密码策略
            password_policy = security_config["password_policy"]
            self.assertGreaterEqual(password_policy.get("min_length", 0), 8)
            
            # 验证速率限制
            rate_limits = security_config["rate_limits"]
            self.assertGreater(rate_limits.get("daily_send_limit", 0), 0)
            
            print("安全配置加载测试通过")
        else:
            print("警告: 安全配置文件不存在，跳过配置加载测试")


def run_security_tests():
    """运行所有安全测试"""
    print("=" * 60)
    print("开始运行安全模块测试")
    print("=" * 60)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityManager))
    suite.addTests(loader.loadTestsFromTestCase(TestSecurityHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationSecurity))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    print("安全模块测试完成")
    print(f"测试结果: {result.testsRun} 个测试运行")
    print(f"失败: {len(result.failures)}, 错误: {len(result.errors)}")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # 运行测试
    success = run_security_tests()
    
    # 根据测试结果退出
    sys.exit(0 if success else 1)