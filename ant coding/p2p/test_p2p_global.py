#!/usr/bin/env python3
"""
P2P Global Email System - Unit Tests
测试所有核心功能
"""

import unittest
import asyncio
import json
import base64
import time
import os
import sys

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from p2p_global import (
    GlobalEncryption,
    ICECandidate,
    DHT,
    DHTNode,
    EmailMessage,
    Mailbox,
    Identity,
    GlobalP2PNode,
    P2PEmailNode
)


class TestGlobalEncryption(unittest.TestCase):
    """测试加密模块"""
    
    def setUp(self):
        """设置测试环境"""
        self.enc1 = GlobalEncryption()
        self.enc2 = GlobalEncryption()
        
        # 交换密钥
        self.enc1.derive_shared_secret(self.enc2.get_public_key_bytes(), "node2")
        self.enc2.derive_shared_secret(self.enc1.get_public_key_bytes(), "node1")
    
    def test_public_key_generation(self):
        """测试公钥生成"""
        pubkey = self.enc1.get_public_key_bytes()
        self.assertEqual(len(pubkey), 32, "公钥应该是32字节")
        self.assertIsInstance(pubkey, bytes, "公钥应该是bytes类型")
    
    def test_shared_secret_derivation(self):
        """测试共享密钥派生"""
        secret = self.enc1.shared_secrets.get("node2")
        self.assertIsNotNone(secret, "应该能派生共享密钥")
        self.assertEqual(len(secret), 32, "共享密钥应该是32字节")
        
        # 对称性测试
        secret2 = self.enc2.shared_secrets.get("node1")
        self.assertEqual(secret, secret2, "双方派生的共享密钥应该相同")
    
    def test_encrypt_decrypt(self):
        """测试加密解密"""
        message = "Hello, P2P World!"
        
        # 加密
        encrypted = self.enc1.encrypt(message, "node2")
        self.assertIsInstance(encrypted, str, "加密结果应该是字符串")
        self.assertGreater(len(encrypted), 0, "加密结果不应为空")
        
        # 解密
        decrypted = self.enc2.decrypt(encrypted, "node1")
        self.assertEqual(decrypted, message, "解密后的消息应该与原文相同")
    
    def test_encrypt_different_messages(self):
        """测试不同消息产生不同密文"""
        msg1 = "Message 1"
        msg2 = "Message 2"
        
        enc1 = self.enc1.encrypt(msg1, "node2")
        enc2 = self.enc1.encrypt(msg2, "node2")
        
        self.assertNotEqual(enc1, enc2, "不同消息应该产生不同密文")
    
    def test_no_shared_secret_error(self):
        """测试没有共享密钥时的错误"""
        enc3 = GlobalEncryption()
        
        with self.assertRaises(ValueError, msg="没有共享密钥时应抛出异常"):
            self.enc1.encrypt("test", "node3")


class TestIdentity(unittest.TestCase):
    """测试身份模块"""
    
    def test_keypair_generation(self):
        """测试密钥对生成"""
        priv, pub = Identity.generate_keypair()
        self.assertEqual(len(priv), 32, "私钥应该是32字节")
        self.assertEqual(len(pub), 32, "公钥应该是32字节")
    
    def test_pubkey_to_id(self):
        """测试公钥转ID"""
        _, pub = Identity.generate_keypair()
        node_id = Identity.pubkey_to_id(pub)
        self.assertEqual(len(node_id), 40, "节点ID应该是40字符")
        self.assertTrue(all(c in '0123456789abcdef' for c in node_id), "ID应该是hex格式")
    
    def test_id_from_seed(self):
        """测试从种子生成ID"""
        seed1 = "user@example.com"
        seed2 = "user@example.com"
        seed3 = "other@example.com"
        
        _, pub1 = Identity.id_from_seed(seed1)
        _, pub2 = Identity.id_from_seed(seed2)
        _, pub3 = Identity.id_from_seed(seed3)
        
        id1 = Identity.pubkey_to_id(pub1)
        id2 = Identity.pubkey_to_id(pub2)
        id3 = Identity.pubkey_to_id(pub3)
        
        self.assertEqual(id1, id2, "相同种子应该产生相同ID")
        self.assertNotEqual(id1, id3, "不同种子应该产生不同ID")


class TestICECandidate(unittest.TestCase):
    """测试ICE候选"""
    
    def test_candidate_creation(self):
        """测试候选创建"""
        candidate = ICECandidate(
            type='host',
            ip='192.168.1.1',
            port=8000,
            protocol='udp',
            region='local',
            priority=100
        )
        
        self.assertEqual(candidate.type, 'host')
        self.assertEqual(candidate.ip, '192.168.1.1')
        self.assertEqual(candidate.port, 8000)
    
    def test_candidate_to_dict(self):
        """测试候选序列化"""
        candidate = ICECandidate(
            type='tls443',
            ip='1.2.3.4',
            port=443,
            protocol='tls',
            fake_domain='www.google.com',
            sni='www.google.com'
        )
        
        data = candidate.to_dict()
        self.assertEqual(data['type'], 'tls443')
        self.assertEqual(data['fake_domain'], 'www.google.com')
        self.assertEqual(data['sni'], 'www.google.com')
    
    def test_candidate_from_dict(self):
        """测试候选反序列化"""
        data = {
            'type': 'srflx',
            'ip': '8.8.8.8',
            'port': 19302,
            'protocol': 'udp',
            'region': 'us',
            'priority': 80,
            'latency': 50.0
        }
        
        candidate = ICECandidate.from_dict(data)
        self.assertEqual(candidate.type, 'srflx')
        self.assertEqual(candidate.latency, 50.0)


class TestDHT(unittest.TestCase):
    """测试DHT网络"""
    
    def setUp(self):
        """设置测试环境"""
        self.dht = DHT("aabbccddeeff00112233445566778899aabbccdd")
    
    def test_distance_calculation(self):
        """测试距离计算"""
        id1 = "0000000000000000000000000000000000000001"
        id2 = "0000000000000000000000000000000000000002"
        
        dist = self.dht._distance(id1, id2)
        self.assertEqual(dist, 3, "XOR距离应该正确")
    
    def test_add_node(self):
        """测试添加节点"""
        node = DHTNode(
            node_id="ffee001122334455667788990011223344556677",
            ip="192.168.1.2",
            port=8001
        )
        
        self.dht.add_node(node)
        bucket_idx = self.dht._bucket_index(node.node_id)
        self.assertIn(node.node_id, self.dht.buckets[bucket_idx])
    
    def test_get_nodes(self):
        """测试获取节点"""
        # 添加多个节点
        for i in range(5):
            node = DHTNode(
                node_id=f"{i:040x}",
                ip=f"192.168.1.{i+1}",
                port=8000 + i
            )
            self.dht.add_node(node)
        
        # 获取最近节点
        target_id = "0000000000000000000000000000000000000001"
        nodes = self.dht.get_nodes(target_id, count=3)
        
        self.assertLessEqual(len(nodes), 3, "应该返回指定数量的节点")
    
    def test_store_and_get_data(self):
        """测试数据存储"""
        key = "test_key"
        value = b"test_value"
        
        self.dht.put(key, value, ttl=3600)
        retrieved = self.dht.get(key)
        
        self.assertEqual(retrieved, value, "存储和检索的值应该相同")
    
    def test_expired_data(self):
        """测试过期数据"""
        key = "test_expired_key"
        value = b"test_value"
        
        # 存储一个1秒后过期的数据
        self.dht.put(key, value, ttl=1)
        time.sleep(1.1)
        
        retrieved = self.dht.get(key)
        self.assertIsNone(retrieved, "过期数据应该返回None")


class TestEmailMessage(unittest.TestCase):
    """测试邮件消息"""
    
    def test_message_creation(self):
        """测试邮件创建"""
        message = EmailMessage(
            message_id="msg_123",
            sender_id="sender_abc",
            recipient_id="recipient_xyz",
            subject="Test Subject",
            body="Test Body",
            timestamp=time.time()
        )
        
        self.assertEqual(message.subject, "Test Subject")
        self.assertFalse(message.read)
    
    def test_message_serialization(self):
        """测试邮件序列化"""
        message = EmailMessage(
            message_id="msg_456",
            sender_id="sender_def",
            recipient_id="recipient_uvw",
            subject="Serialization Test",
            body="Serialization Body",
            timestamp=1234567890.0,
            read=True,
            attachments=["file1.pdf", "file2.jpg"]
        )
        
        # 序列化
        data = message.to_dict()
        self.assertEqual(data['subject'], "Serialization Test")
        self.assertTrue(data['read'])
        
        # 反序列化
        restored = EmailMessage.from_dict(data)
        self.assertEqual(restored.message_id, message.message_id)
        self.assertEqual(restored.subject, message.subject)
        self.assertTrue(restored.read)


class TestMailbox(unittest.TestCase):
    """测试邮箱"""
    
    def setUp(self):
        """设置测试环境"""
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.mailbox = Mailbox("test_user", self.temp_dir)
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_add_inbox(self):
        """测试添加收件"""
        message = EmailMessage(
            message_id="inbox_001",
            sender_id="sender_1",
            recipient_id="test_user",
            subject="Test Inbox",
            body="Test Inbox Body",
            timestamp=time.time()
        )
        
        self.mailbox.add_inbox(message)
        inbox = self.mailbox.get_inbox()
        
        self.assertEqual(len(inbox), 1)
        self.assertEqual(inbox[0].subject, "Test Inbox")
    
    def test_add_sent(self):
        """测试添加已发送"""
        message = EmailMessage(
            message_id="sent_001",
            sender_id="test_user",
            recipient_id="recipient_1",
            subject="Test Sent",
            body="Test Sent Body",
            timestamp=time.time()
        )
        
        self.mailbox.add_sent(message)
        sent = self.mailbox.get_sent()
        
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0].subject, "Test Sent")
    
    def test_mark_read(self):
        """测试标记已读"""
        message = EmailMessage(
            message_id="unread_001",
            sender_id="sender_1",
            recipient_id="test_user",
            subject="Unread Test",
            body="Unread Body",
            timestamp=time.time(),
            read=False
        )
        
        self.mailbox.add_inbox(message)
        unread_count = self.mailbox.get_unread_count()
        self.assertEqual(unread_count, 1)
        
        self.mailbox.mark_read(message.message_id)
        unread_count = self.mailbox.get_unread_count()
        self.assertEqual(unread_count, 0)
    
    def test_delete_message(self):
        """测试删除邮件"""
        message = EmailMessage(
            message_id="delete_001",
            sender_id="sender_1",
            recipient_id="test_user",
            subject="Delete Test",
            body="Delete Body",
            timestamp=time.time()
        )
        
        self.mailbox.add_inbox(message)
        self.assertEqual(len(self.mailbox.get_inbox()), 1)
        
        self.mailbox.delete(message.message_id)
        self.assertEqual(len(self.mailbox.get_inbox()), 0)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_encryption_integration(self):
        """测试加密模块集成"""
        enc1 = GlobalEncryption()
        enc2 = GlobalEncryption()
        
        # 交换密钥
        enc1.derive_shared_secret(enc2.get_public_key_bytes(), "node2")
        enc2.derive_shared_secret(enc1.get_public_key_bytes(), "node1")
        
        # 测试多条消息
        messages = [
            "Hello",
            "This is a longer message",
            "Unicode: 你好世界 🌍",
            "Special chars: !@#$%^&*()"
        ]
        
        for msg in messages:
            encrypted = enc1.encrypt(msg, "node2")
            decrypted = enc2.decrypt(encrypted, "node1")
            self.assertEqual(decrypted, msg, f"消息 '{msg}' 加密解密失败")
    
    def test_dht_integration(self):
        """测试DHT集成"""
        dht1 = DHT("1111" + "0" * 36)
        dht2 = DHT("2222" + "0" * 36)
        
        # 添加节点
        node = DHTNode("2222" + "0" * 36, "192.168.1.2", 8001)
        dht1.add_node(node)
        
        # 存储和检索数据
        key = "pubkey:node3"
        value = b"test_public_key_bytes"
        dht1.put(key, value)
        
        retrieved = dht1.get(key)
        self.assertEqual(retrieved, value)


def run_tests():
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalEncryption))
    suite.addTests(loader.loadTestsFromTestCase(TestIdentity))
    suite.addTests(loader.loadTestsFromTestCase(TestICECandidate))
    suite.addTests(loader.loadTestsFromTestCase(TestDHT))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailMessage))
    suite.addTests(loader.loadTestsFromTestCase(TestMailbox))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回结果
    return result.wasSuccessful()


if __name__ == "__main__":
    print("=" * 70)
    print("P2P Global Email System - Unit Tests")
    print("=" * 70)
    print()
    
    success = run_tests()
    
    print()
    print("=" * 70)
    if success:
        print("[OK] 所有测试通过!")
    else:
        print("[FAILED] 部分测试失败!")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
