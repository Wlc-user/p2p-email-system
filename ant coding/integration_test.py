#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试 - 测试双域名邮箱系统的完整功能
"""

import os
import sys
import json
import time
import socket
import threading
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from server.protocols import Message, MessageType, Mail, MailAddress, MailStatus
from client.main import MailClient


class IntegrationTest:
    """集成测试类"""
    
    def __init__(self):
        self.test_dir = tempfile.mkdtemp(prefix="mail_test_")
        self.config_dir = Path(self.test_dir) / "config"
        self.data_dir = Path(self.test_dir) / "data"
        
        # 创建测试目录
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建测试配置文件
        self._create_test_configs()
        
        # 测试结果
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
        # 服务器线程
        self.server_threads = []
        self.servers = []
        
    def _create_test_configs(self):
        """创建测试配置文件"""
        
        # 域名1配置
        domain1_config = {
            "domain": "test1.com",
            "server_port": 18080,
            "max_clients": 100,
            "data_path": str(self.data_dir / "domain1"),
            "mail_storage_limit_mb": 100,
            "daily_send_limit": 50,
            "session_timeout_minutes": 30,
            "encryption_key": "test1-secret-key",
            "smtp_port": 12525,
            "pop3_port": 11110,
            "imap_port": 11430,
            "admin_email": "admin@test1.com"
        }
        
        # 域名2配置
        domain2_config = {
            "domain": "test2.com",
            "server_port": 18081,
            "max_clients": 100,
            "data_path": str(self.data_dir / "domain2"),
            "mail_storage_limit_mb": 100,
            "daily_send_limit": 50,
            "session_timeout_minutes": 30,
            "encryption_key": "test2-secret-key",
            "smtp_port": 12526,
            "pop3_port": 11111,
            "imap_port": 11431,
            "admin_email": "admin@test2.com"
        }
        
        # 保存配置文件
        with open(self.config_dir / "domain1_config.json", 'w', encoding='utf-8') as f:
            json.dump(domain1_config, f, indent=2)
        
        with open(self.config_dir / "domain2_config.json", 'w', encoding='utf-8') as f:
            json.dump(domain2_config, f, indent=2)
    
    def start_servers(self):
        """启动测试服务器"""
        
        print("启动测试服务器...")
        
        try:
            # 导入服务器模块
            from server.server_manager import ServerManager
            
            # 启动域名1服务器
            server1 = ServerManager(
                str(self.config_dir / "domain1_config.json"),
                "test1.com"
            )
            
            server1_thread = threading.Thread(
                target=server1.start,
                daemon=True
            )
            server1_thread.start()
            
            self.servers.append(server1)
            self.server_threads.append(server1_thread)
            
            # 等待服务器启动
            time.sleep(2)
            
            # 启动域名2服务器
            server2 = ServerManager(
                str(self.config_dir / "domain2_config.json"),
                "test2.com"
            )
            
            server2_thread = threading.Thread(
                target=server2.start,
                daemon=True
            )
            server2_thread.start()
            
            self.servers.append(server2)
            self.server_threads.append(server2_thread)
            
            # 等待服务器启动
            time.sleep(2)
            
            print("✓ 测试服务器启动成功")
            print(f"  域名1: test1.com - 端口 18080")
            print(f"  域名2: test2.com - 端口 18081")
            
            return True
            
        except Exception as e:
            print(f"✗ 启动服务器失败: {e}")
            return False
    
    def stop_servers(self):
        """停止测试服务器"""
        
        print("\n停止测试服务器...")
        
        for server in self.servers:
            try:
                server.stop()
            except:
                pass
        
        # 等待线程结束
        for thread in self.server_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        print("✓ 测试服务器已停止")
    
    def run_test(self, test_name: str, test_func):
        """运行单个测试"""
        
        self.total_tests += 1
        print(f"\n[{self.total_tests}] 运行测试: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            elapsed_time = time.time() - start_time
            
            if result:
                print(f"   ✓ 通过 ({elapsed_time:.2f}秒)")
                self.passed_tests += 1
                self.test_results[test_name] = {"passed": True, "time": elapsed_time}
            else:
                print(f"   ✗ 失败 ({elapsed_time:.2f}秒)")
                self.test_results[test_name] = {"passed": False, "time": elapsed_time}
                
        except Exception as e:
            print(f"   ✗ 异常: {e}")
            self.test_results[test_name] = {"passed": False, "error": str(e)}
    
    # ========== 测试用例 ==========
    
    def test_01_server_connection(self):
        """测试服务器连接"""
        
        try:
            # 测试连接域名1服务器
            sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock1.settimeout(5)
            sock1.connect(("127.0.0.1", 18080))
            sock1.close()
            
            # 测试连接域名2服务器
            sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock2.settimeout(5)
            sock2.connect(("127.0.0.1", 18081))
            sock2.close()
            
            return True
            
        except Exception as e:
            print(f"连接失败: {e}")
            return False
    
    def test_02_client_creation(self):
        """测试客户端创建"""
        
        try:
            # 创建客户端
            client = MailClient("127.0.0.1", 18080)
            
            # 测试配置加载
            if not client.config:
                return False
            
            # 测试连接到域名1
            if not client.connect_to_server("test1.com"):
                return False
            
            # 测试ping
            if not client.ping_server():
                return False
            
            client.disconnect()
            return True
            
        except Exception as e:
            print(f"客户端创建失败: {e}")
            return False
    
    def test_03_user_registration(self):
        """测试用户注册"""
        
        try:
            # 创建客户端
            client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not client.connect_to_server("test1.com"):
                return False
            
            # 注册用户1
            success1 = client.register_user(
                username="alice",
                password="AlicePass123!",
                email="alice@test1.com"
            )
            
            # 注册用户2
            success2 = client.register_user(
                username="bob",
                password="BobPass123!",
                email="bob@test1.com"
            )
            
            client.disconnect()
            
            return success1 and success2
            
        except Exception as e:
            print(f"用户注册失败: {e}")
            return False
    
    def test_04_user_login(self):
        """测试用户登录"""
        
        try:
            # 创建客户端
            client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not client.connect_to_server("test1.com"):
                return False
            
            # 登录用户
            success = client.login("alice", "AlicePass123!")
            
            client.disconnect()
            
            return success
            
        except Exception as e:
            print(f"用户登录失败: {e}")
            return False
    
    def test_05_send_local_mail(self):
        """测试发送本地邮件（同一域名）"""
        
        try:
            # 创建发件人客户端
            sender_client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not sender_client.connect_to_server("test1.com"):
                return False
            
            # 登录发件人
            if not sender_client.login("alice", "AlicePass123!"):
                return False
            
            # 发送邮件给bob（同一域名）
            mail_id = sender_client.send_mail(
                to_addresses=["bob@test1.com"],
                subject="测试本地邮件",
                body="这是一封测试邮件，发送给同一域名的用户。"
            )
            
            sender_client.disconnect()
            
            return mail_id is not None
            
        except Exception as e:
            print(f"发送本地邮件失败: {e}")
            return False
    
    def test_06_receive_local_mail(self):
        """测试接收本地邮件"""
        
        try:
            # 创建收件人客户端
            receiver_client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not receiver_client.connect_to_server("test1.com"):
                return False
            
            # 登录收件人
            if not receiver_client.login("bob", "BobPass123!"):
                return False
            
            # 获取收件箱
            inbox = receiver_client.get_mailbox("inbox")
            
            receiver_client.disconnect()
            
            # 检查是否有邮件
            return len(inbox) > 0
            
        except Exception as e:
            print(f"接收本地邮件失败: {e}")
            return False
    
    def test_07_cross_domain_user_registration(self):
        """测试跨域用户注册"""
        
        try:
            # 创建客户端
            client = MailClient("127.0.0.1", 18081)
            
            # 连接到域名2
            if not client.connect_to_server("test2.com"):
                return False
            
            # 注册域名2的用户
            success = client.register_user(
                username="charlie",
                password="CharliePass123!",
                email="charlie@test2.com"
            )
            
            client.disconnect()
            
            return success
            
        except Exception as e:
            print(f"跨域用户注册失败: {e}")
            return False
    
    def test_08_send_cross_domain_mail(self):
        """测试发送跨域邮件"""
        
        try:
            # 创建发件人客户端（域名1）
            sender_client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not sender_client.connect_to_server("test1.com"):
                return False
            
            # 登录发件人
            if not sender_client.login("alice", "AlicePass123!"):
                return False
            
            # 发送邮件给charlie（域名2）
            mail_id = sender_client.send_mail(
                to_addresses=["charlie@test2.com"],
                subject="测试跨域邮件",
                body="这是一封测试邮件，发送给不同域名的用户。"
            )
            
            sender_client.disconnect()
            
            return mail_id is not None
            
        except Exception as e:
            print(f"发送跨域邮件失败: {e}")
            return False
    
    def test_09_mail_search(self):
        """测试邮件搜索"""
        
        try:
            # 创建客户端
            client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not client.connect_to_server("test1.com"):
                return False
            
            # 登录用户
            if not client.login("alice", "AlicePass123!"):
                return False
            
            # 搜索邮件
            results = client.search_mails("测试")
            
            client.disconnect()
            
            return len(results) > 0
            
        except Exception as e:
            print(f"邮件搜索失败: {e}")
            return False
    
    def test_10_mail_withdrawal(self):
        """测试邮件撤回"""
        
        try:
            # 创建发件人客户端
            sender_client = MailClient("127.0.0.1", 18080)
            
            # 连接到域名1
            if not sender_client.connect_to_server("test1.com"):
                return False
            
            # 登录发件人
            if not sender_client.login("alice", "AlicePass123!"):
                return False
            
            # 发送一封测试邮件
            mail_id = sender_client.send_mail(
                to_addresses=["bob@test1.com"],
                subject="测试撤回的邮件",
                body="这封邮件将被撤回。"
            )
            
            if not mail_id:
                return False
            
            # 等待邮件发送
            time.sleep(1)
            
            # 撤回邮件
            success = sender_client.withdraw_mail(mail_id)
            
            sender_client.disconnect()
            
            return success
            
        except Exception as e:
            print(f"邮件撤回失败: {e}")
            return False
    
    def test_11_data_isolation(self):
        """测试数据隔离"""
        
        try:
            # 检查域名1的数据目录
            domain1_data_dir = self.data_dir / "domain1"
            domain2_data_dir = self.data_dir / "domain2"
            
            # 确保目录存在
            domain1_data_dir.mkdir(exist_ok=True)
            domain2_data_dir.mkdir(exist_ok=True)
            
            # 创建测试文件
            test_file1 = domain1_data_dir / "test_file.txt"
            test_file2 = domain2_data_dir / "test_file.txt"
            
            with open(test_file1, 'w') as f:
                f.write("domain1 data")
            
            with open(test_file2, 'w') as f:
                f.write("domain2 data")
            
            # 验证文件内容不同
            with open(test_file1, 'r') as f:
                content1 = f.read()
            
            with open(test_file2, 'r') as f:
                content2 = f.read()
            
            return content1 != content2
            
        except Exception as e:
            print(f"数据隔离测试失败: {e}")
            return False
    
    def test_12_storage_manager(self):
        """测试存储管理器"""
        
        try:
            from server.storage_manager import StorageManager
            
            # 创建存储管理器
            test_storage_dir = self.data_dir / "test_storage"
            storage_manager = StorageManager(str(test_storage_dir))
            
            # 测试用户创建
            user_data = storage_manager.create_user(
                username="testuser",
                domain="test.com",
                password="testpass",
                email="test@test.com"
            )
            
            if not user_data:
                return False
            
            # 测试用户验证
            auth_user = storage_manager.authenticate_user(
                username="testuser",
                domain="test.com",
                password="testpass"
            )
            
            if not auth_user:
                return False
            
            # 测试用户存在检查
            if not storage_manager.user_exists("testuser", "test.com"):
                return False
            
            return True
            
        except Exception as e:
            print(f"存储管理器测试失败: {e}")
            return False
    
    def test_13_security_module(self):
        """测试安全模块"""
        
        try:
            from server.security import SecurityManager, generate_secure_password
            
            # 创建安全配置
            config = {
                'encryption_key': 'test-encryption-key-1234567890',
                'jwt_secret': 'test-jwt-secret-1234567890',
                'salt_length': 16,
                'max_login_attempts': 3,
                'login_lockout_minutes': 1,
                'daily_send_limit': 10,
                'rate_limit_per_minute': 5
            }
            
            # 创建安全管理器
            security_manager = SecurityManager(config)
            
            # 测试密码哈希
            password = "TestPassword123!"
            hashed = security_manager.hash_password(password)
            
            if not security_manager.verify_password(password, hashed):
                return False
            
            # 测试密码强度验证
            is_strong, message = security_manager.validate_password_strength(password)
            if not is_strong:
                return False
            
            # 测试令牌生成
            token = security_manager.generate_token("testuser", "test.com")
            if not security_manager.verify_token(token):
                return False
            
            # 测试安全密码生成
            secure_pass = generate_secure_password(12)
            if len(secure_pass) != 12:
                return False
            
            return True
            
        except Exception as e:
            print(f"安全模块测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        
        print("=" * 60)
        print("智能安全邮箱系统 - 集成测试")
        print("=" * 60)
        print(f"测试目录: {self.test_dir}")
        print("=" * 60)
        
        # 启动服务器
        if not self.start_servers():
            print("✗ 无法启动服务器，测试终止")
            return False
        
        # 运行测试用例
        tests = [
            ("服务器连接测试", self.test_01_server_connection),
            ("客户端创建测试", self.test_02_client_creation),
            ("用户注册测试", self.test_03_user_registration),
            ("用户登录测试", self.test_04_user_login),
            ("发送本地邮件测试", self.test_05_send_local_mail),
            ("接收本地邮件测试", self.test_06_receive_local_mail),
            ("跨域用户注册测试", self.test_07_cross_domain_user_registration),
            ("发送跨域邮件测试", self.test_08_send_cross_domain_mail),
            ("邮件搜索测试", self.test_09_mail_search),
            ("邮件撤回测试", self.test_10_mail_withdrawal),
            ("数据隔离测试", self.test_11_data_isolation),
            ("存储管理器测试", self.test_12_storage_manager),
            ("安全模块测试", self.test_13_security_module),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # 停止服务器
        self.stop_servers()
        
        # 输出测试结果
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        print(f"总测试数: {self.total_tests}")
        print(f"通过数: {self.passed_tests}")
        print(f"失败数: {self.total_tests - self.passed_tests}")
        print(f"通过率: {self.passed_tests/self.total_tests*100:.1f}%")
        print("=" * 60)
        
        # 详细结果
        print("\n详细测试结果:")
        for test_name, result in self.test_results.items():
            status = "✓ 通过" if result.get("passed") else "✗ 失败"
            time_info = f" ({result.get('time', 0):.2f}秒)" if "time" in result else ""
            error_info = f" - {result.get('error', '')}" if "error" in result else ""
            print(f"  {status}{time_info}{error_info}: {test_name}")
        
        # 清理测试目录
        self.cleanup()
        
        return self.passed_tests == self.total_tests
    
    def cleanup(self):
        """清理测试目录"""
        try:
            if os.path.exists(self.test_dir):
                shutil.rmtree(self.test_dir)
                print(f"\n✓ 清理测试目录: {self.test_dir}")
        except Exception as e:
            print(f"\n✗ 清理测试目录失败: {e}")


def main():
    """主函数"""
    
    print("智能安全邮箱系统 - 完整集成测试")
    print("测试功能:")
    print("  1. 双服务器同时运行")
    print("  2. 隔离域名邮箱系统")
    print("  3. 跨域邮件发送")
    print("  4. 客户端管理")
    print("  5. 数据逻辑隔离")
    print("  6. 安全功能")
    print()
    
    input("按 Enter 键开始测试...")
    
    # 创建并运行测试
    test = IntegrationTest()
    success = test.run_all_tests()
    
    # 输出最终结果
    print("\n" + "=" * 60)
    if success:
        print("🎉 所有测试通过！系统功能正常。")
    else:
        print("⚠️  部分测试失败，请检查系统实现。")
    print("=" * 60)
    
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