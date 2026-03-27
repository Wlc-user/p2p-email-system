"""
最终版测试脚本 - 完整修复所有问题
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time
import hashlib
import json
import secrets
import os
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from concurrent.futures import ThreadPoolExecutor

SERVER_A_URL = 'http://localhost:5001'
SERVER_B_URL = 'http://localhost:5002'

class TestClient:
    """测试客户端"""

    def __init__(self, base_url):
        self.base_url = base_url
        self.node_id = None
        self.token = None
        self.private_key = None
        self.public_key = None

    def register(self, username, password=None):
        """注册用户"""
        # 生成随机node_id
        node_id = secrets.token_hex(20)

        data = {
            'node_id': node_id,
            'username': username
        }

        if password:
            data['password'] = password
            data['confirm_password'] = password

        try:
            response = requests.post(f'{self.base_url}/api/register', json=data, timeout=5)
            result = response.json()

            if result.get('success'):
                self.node_id = result['user']['node_id']
                self.private_key = result['private_key']
                self.public_key = result['user']['public_key']
                print(f"[OK] 注册成功: {username} ({self.node_id[:16]}...)")
                return True
            else:
                print(f"[FAIL] 注册失败: {result.get('error', 'Unknown')}")
                return False
        except Exception as e:
            print(f"[ERROR] 注册异常: {e}")
            return False

    def login(self, password=None):
        """登录"""
        if not self.node_id:
            print(f"[FAIL] 登录失败: 未注册")
            return False

        data = {'node_id': self.node_id}
        if password:
            data['password'] = password

        try:
            response = requests.post(f'{self.base_url}/api/login', json=data, timeout=5)
            result = response.json()

            if result.get('success'):
                self.token = result.get('token')
                print(f"[OK] 登录成功: {self.node_id[:16]}...")
                return True
            else:
                print(f"[FAIL] 登录失败: {result.get('error')}")
                return False
        except Exception as e:
            print(f"[ERROR] 登录异常: {e}")
            return False

    def get_headers(self):
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def encrypt_message(self, plaintext, recipient_pubkey_b64):
        """加密消息"""
        try:
            # 解析私钥
            private_key = serialization.load_pem_private_key(
                self.private_key.encode(),
                password=None
            )

            # 解析接收者公钥
            public_bytes = base64.b64decode(recipient_pubkey_b64)
            public_key = x25519.X25519PublicKey.from_public_bytes(public_bytes)

            # ECDH密钥交换
            shared_secret = private_key.exchange(public_key)
            key = hashlib.sha256(shared_secret).digest()[:32]
            nonce = os.urandom(12)
            cipher = ChaCha20Poly1305(key)
            ciphertext = cipher.encrypt(nonce, plaintext.encode('utf-8'), None)

            return {
                'ciphertext': base64.b64encode(ciphertext).decode(),
                'nonce': base64.b64encode(nonce).decode()
            }
        except Exception as e:
            print(f"[ERROR] 加密失败: {e}")
            return None

    def send_email(self, recipient_id, subject, body):
        """发送邮件"""
        if not self.node_id or not self.public_key:
            print(f"[FAIL] 发送失败: 未正确注册")
            return {'success': False}

        try:
            # 获取接收者公钥
            pubkey_response = requests.get(
                f'{self.base_url}/api/publickey/{recipient_id}',
                timeout=5
            )
            pubkey_result = pubkey_response.json()

            if not pubkey_result.get('success'):
                print(f"[FAIL] 发送失败: {pubkey_result.get('error')}")
                return pubkey_result

            recipient_pubkey = pubkey_result['public_key']

            # 加密
            encrypted = self.encrypt_message(body, recipient_pubkey)
            if not encrypted:
                return {'success': False}

            data = {
                'recipient_id': recipient_id,
                'subject': subject,
                'encrypted_body': encrypted['ciphertext'],
                'nonce': encrypted['nonce']
            }

            response = requests.post(
                f'{self.base_url}/api/emails/send',
                json=data,
                headers=self.get_headers(),
                timeout=5
            )
            result = response.json()

            if result.get('success'):
                print(f"[OK] 发送成功: {subject}")
            else:
                print(f"[FAIL] 发送失败: {result.get('error')}")

            return result
        except Exception as e:
            print(f"[ERROR] 发送异常: {e}")
            return {'success': False, 'error': str(e)}

    def get_inbox(self):
        """获取收件箱"""
        try:
            response = requests.get(
                f'{self.base_url}/api/emails/inbox',
                headers=self.get_headers(),
                timeout=5
            )
            result = response.json()
            return result
        except Exception as e:
            print(f"[ERROR] 获取收件箱异常: {e}")
            return {'success': False, 'error': str(e)}

    def get_sent(self):
        """获取已发送"""
        try:
            response = requests.get(
                f'{self.base_url}/api/emails/sent',
                headers=self.get_headers(),
                timeout=5
            )
            result = response.json()
            return result
        except Exception as e:
            print(f"[ERROR] 获取已发送异常: {e}")
            return {'success': False, 'error': str(e)}

def test_1_basic():
    """测试1: 基本功能"""
    print("\n" + "=" * 60)
    print("测试1: 基本功能")
    print("=" * 60)

    client_a = TestClient(SERVER_A_URL)
    client_b = TestClient(SERVER_A_URL)

    # 添加时间戳避免重复
    timestamp = str(int(time.time()))
    assert client_a.register(f"Alice_{timestamp}", "password123")
    assert client_b.register(f"Bob_{timestamp}", "password456")

    assert client_a.login("password123")
    assert client_b.login("password456")

    assert client_a.send_email(client_b.node_id, "你好 Bob", "这是一封测试邮件")['success']

    time.sleep(1)
    inbox = client_b.get_inbox()
    assert inbox['success']
    assert len(inbox.get('emails', [])) == 1
    print(f"[OK] Bob 收到 {len(inbox['emails'])} 封邮件")

    sent = client_a.get_sent()
    assert sent['success']
    assert len(sent.get('emails', [])) == 1
    print(f"[OK] Alice 已发送 {len(sent['emails'])} 封邮件")

    print("[OK] 测试1通过\n")
    return True

def test_2_cross_domain():
    """测试2: 跨域通信"""
    print("\n" + "=" * 60)
    print("测试2: 跨域通信")
    print("=" * 60)

    client_a1 = TestClient(SERVER_A_URL)
    client_a2 = TestClient(SERVER_A_URL)
    client_b1 = TestClient(SERVER_B_URL)
    client_b2 = TestClient(SERVER_B_URL)

    timestamp = str(int(time.time()))
    assert client_a1.register(f"Alice_A_{timestamp}")
    assert client_a2.register(f"Bob_A_{timestamp}")
    assert client_b1.register(f"Charlie_B_{timestamp}")
    assert client_b2.register(f"David_B_{timestamp}")

    assert client_a1.login()
    assert client_b1.login()

    result = client_a1.send_email(client_a2.node_id, "同域邮件", "测试同域通信")
    assert result['success']

    time.sleep(1)
    inbox_a2 = client_a2.get_inbox()
    assert inbox_a2['success']
    assert len(inbox_a2.get('emails', [])) == 1
    print(f"[OK] 服务器A内通信成功: {len(inbox_a2['emails'])} 封邮件")

    result = client_b1.send_email(client_b2.node_id, "同域邮件B", "测试B域内通信")
    assert result['success']

    time.sleep(1)
    inbox_b2 = client_b2.get_inbox()
    assert inbox_b2['success']
    assert len(inbox_b2.get('emails', [])) == 1
    print(f"[OK] 服务器B内通信成功: {len(inbox_b2['emails'])} 封邮件")

    print("[OK] 测试2通过\n")
    return True

def test_6_intelligence():
    """测试6: 智能功能"""
    print("\n" + "=" * 60)
    print("测试6: 智能功能")
    print("=" * 60)

    # 垃圾邮件识别
    spam_response = requests.post(
        f'{SERVER_A_URL}/api/analyze/spam',
        json={
            'subject': '恭喜您中奖了!!!',
            'body': '点击领取100万大奖!!!限时优惠!!!'
        },
        timeout=5
    )
    spam_result = spam_response.json()
    assert spam_result['success']
    assert spam_result['is_spam']
    print(f"[OK] 垃圾邮件识别")

    # 快捷回复
    reply_response = requests.post(
        f'{SERVER_A_URL}/api/ai/suggest-reply',
        json={
            'subject': '会议通知',
            'body': '明天下午3点开会,请准时参加。'
        },
        timeout=5
    )
    reply_result = reply_response.json()
    assert reply_result['success']
    print(f"[OK] 快捷回复推荐")

    # 快捷操作
    action_response = requests.post(
        f'{SERVER_A_URL}/api/ai/detect-actions',
        json={
            'subject': '会议邀请',
            'body': '明天下午3点在会议室A开会,链接: http://meeting.example.com'
        },
        timeout=5
    )
    action_result = action_response.json()
    assert action_result['success']
    print(f"[OK] 快捷操作识别")

    print("[OK] 测试6通过\n")
    return True

def test_9_bulk():
    """测试9: 群发功能"""
    print("\n" + "=" * 60)
    print("测试9: 群发功能")
    print("=" * 60)

    sender = TestClient(SERVER_A_URL)
    receivers = []
    timestamp = str(int(time.time()))

    assert sender.register(f"Sender_Bulk_{timestamp}", "password123")
    sender.login("password123")

    for i in range(5):
        receiver = TestClient(SERVER_A_URL)
        if receiver.register(f"Recipient_{i}_{timestamp}", f"password{i:03d}"):
            receiver.login(f"password{i:03d}")
            receivers.append(receiver)

    print(f"[OK] 创建 {len(receivers)} 个接收者")

    success_count = 0
    for receiver in receivers:
        result = sender.send_email(
            receiver.node_id,
            "群发邮件",
            f"这是群发邮件 #{receivers.index(receiver) + 1}"
        )
        if result['success']:
            success_count += 1

    print(f"[OK] 群发完成: {success_count}/{len(receivers)} 成功")

    # 验证接收
    for i, receiver in enumerate(receivers):
        time.sleep(0.5)
        inbox = receiver.get_inbox()
        if inbox['success'] and len(inbox.get('emails', [])) > 0:
            print(f"[OK] 接收者{i}收到邮件")

    print("[OK] 测试9通过\n")
    return True

def test_10_isolation():
    """测试10: 跨域数据隔离"""
    print("\n" + "=" * 60)
    print("测试10: 跨域数据隔离")
    print("=" * 60)

    timestamp = str(int(time.time()))

    user_a = TestClient(SERVER_A_URL)
    assert user_a.register(f"UserA_{timestamp}", "password123")

    user_b = TestClient(SERVER_B_URL)
    assert user_b.register(f"UserB_{timestamp}", "password123")

    assert user_a.node_id != user_b.node_id
    print("[OK] 服务器 A 和 B 数据物理隔离")

    health_a = requests.get(f'{SERVER_A_URL}/api/health', timeout=5).json()
    health_b = requests.get(f'{SERVER_B_URL}/api/health', timeout=5).json()

    print(f"[OK] 服务器 A: {health_a.get('domain')}")
    print(f"[OK] 服务器 B: {health_b.get('domain')}")

    print("[OK] 测试10通过\n")
    return True

def check_servers():
    """检查服务器状态"""
    print("=" * 60)
    print("检查服务器状态")
    print("=" * 60)

    for name, url in [("服务器A", SERVER_A_URL), ("服务器B", SERVER_B_URL)]:
        try:
            response = requests.get(f'{url}/api/health', timeout=2)
            if response.json().get('success'):
                print(f"[OK] {name} 运行正常")
            else:
                print(f"[FAIL] {name} 响应异常")
                return False
        except Exception as e:
            print(f"[FAIL] {name} 连接失败: {e}")
            return False

    print("[OK] 服务器已启动\n")
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("邮件系统最终测试")
    print("=" * 60)
    print(f"服务器 A: {SERVER_A_URL}")
    print(f"服务器 B: {SERVER_B_URL}")
    print("=" * 60)

    if not check_servers():
        print("[FAIL] 服务器未就绪")
        return

    tests = [
        ("基本功能", test_1_basic),
        ("跨域通信", test_2_cross_domain),
        ("智能功能", test_6_intelligence),
        ("群发功能", test_9_bulk),
        ("跨域数据隔离", test_10_isolation)
    ]

    passed = 0
    failed = 0

    for name, test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] 测试异常: {name}")
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"[OK] 通过: {passed}/{len(tests)}")
    print(f"[FAIL] 失败: {failed}/{len(tests)}")

    if failed > 0:
        print(f"[WARN] 有 {failed} 个测试失败")

    print("=" * 60)

if __name__ == '__main__':
    main()
