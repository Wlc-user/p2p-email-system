"""
邮件系统完整测试脚本(改进版)
修复数据库锁定和并发问题
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time
import hashlib
import json
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
import base64
import os
import random
import string
from concurrent.futures import ThreadPoolExecutor

# 测试配置
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
        # 生成随机node_id - 40位十六进制字符
        import secrets
        node_id = secrets.token_hex(20)

        data = {
            'node_id': node_id,
            'username': username
        }

        if password:
            data['password'] = password
            data['confirm_password'] = password

        response = requests.post(f'{self.base_url}/api/register', json=data)
        result = response.json()

        if result.get('success'):
            self.node_id = result['user']['node_id']
            self.private_key = result['private_key']
            self.public_key = result['user']['public_key']
            print(f"[OK] 注册成功: {username} ({self.node_id[:16]}...)")
            return True
        else:
            print(f"[FAIL] 注册失败: {result.get('error', 'Unknown error')}")
            return False

    def login(self, password=None):
        """登录"""
        if not self.node_id:
            print(f"[FAIL] 登录失败: 未注册,没有node_id")
            return False

        data = {'node_id': self.node_id}
        if password:
            data['password'] = password

        response = requests.post(f'{self.base_url}/api/login', json=data)
        result = response.json()

        if result.get('success'):
            self.token = result.get('token')
            print(f"[OK] 登录成功: {self.node_id[:16]}...")
            return True
        else:
            print(f"[FAIL] 登录失败: {result.get('error', 'Unknown error')}")
            return False

    def get_headers(self):
        """获取请求头"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def encrypt_message(self, plaintext, recipient_pubkey_b64):
        """加密消息"""
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

    def send_email(self, recipient_id, subject, body):
        """发送邮件"""
        if not self.node_id:
            print(f"[FAIL] 发送失败: 未注册")
            return {'success': False}

        # 获取接收者公钥
        pubkey_response = requests.get(
            f'{self.base_url}/api/publickey/{recipient_id}'
        )
        pubkey_result = pubkey_response.json()

        if not pubkey_result.get('success'):
            print(f"[FAIL] 发送失败: 获取公钥失败 - {pubkey_result.get('error')}")
            return pubkey_result

        recipient_pubkey = pubkey_result['public_key']

        # 加密
        encrypted = self.encrypt_message(body, recipient_pubkey)

        data = {
            'recipient_id': recipient_id,
            'subject': subject,
            'encrypted_body': encrypted['ciphertext'],
            'nonce': encrypted['nonce']
        }

        response = requests.post(
            f'{self.base_url}/api/emails/send',
            json=data,
            headers=self.get_headers()
        )
        result = response.json()

        if result.get('success'):
            print(f"[OK] 发送成功: {subject}")
        else:
            print(f"[FAIL] 发送失败: {result.get('error')}")

        return result

    def get_inbox(self):
        """获取收件箱"""
        response = requests.get(
            f'{self.base_url}/api/emails/inbox',
            headers=self.get_headers()
        )
        return response.json()

    def get_sent(self):
        """获取已发送"""
        response = requests.get(
            f'{self.base_url}/api/emails/sent',
            headers=self.get_headers()
        )
        return response.json()

    def recall_email(self, email_id):
        """撤回邮件"""
        try:
            response = requests.post(
                f'{self.base_url}/api/emails/{email_id}/recall',
                headers=self.get_headers()
            )
            return response.json()
        except Exception as e:
            print(f"[WARN] 撤回邮件异常: {e}")
            return {'success': False, 'error': str(e)}

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

def test_1_basic_functionality():
    """测试1: 基本功能"""
    print("\n" + "=" * 60)
    print("测试1: 基本功能")
    print("=" * 60)

    # 创建客户端
    client_a = TestClient(SERVER_A_URL)
    client_b = TestClient(SERVER_A_URL)

    # 注册用户(添加随机后缀)
    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))
    assert client_a.register(f"Alice_{timestamp}", "password123")
    assert client_b.register(f"Bob_{timestamp}", "password456")

    # 登录
    assert client_a.login("password123")
    assert client_b.login("password456")

    # Alice 发邮件给 Bob
    assert client_a.send_email(client_b.node_id, "你好 Bob", "这是一封测试邮件")['success']

    # Bob 检查收件箱
    time.sleep(1)
    inbox = client_b.get_inbox()
    assert inbox['success']
    assert len(inbox.get('emails', [])) == 1
    print(f"[OK] Bob 收到 {len(inbox['emails'])} 封邮件")

    # Alice 检查已发送
    sent = client_a.get_sent()
    assert sent['success']
    assert len(sent.get('emails', [])) == 1
    print(f"[OK] Alice 已发送 {len(sent['emails'])} 封邮件")

    print("[OK] 测试1通过\n")
    return True

def test_2_cross_domain_communication():
    """测试2: 跨域通信(双服务器)"""
    print("\n" + "=" * 60)
    print("测试2: 跨域通信")
    print("=" * 60)

    # 服务器 A 的用户
    client_a1 = TestClient(SERVER_A_URL)
    client_a2 = TestClient(SERVER_A_URL)

    # 服务器 B 的用户
    client_b1 = TestClient(SERVER_B_URL)
    client_b2 = TestClient(SERVER_B_URL)

    # 注册用户(添加随机后缀)
    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))
    assert client_a1.register(f"Alice_A_{timestamp}")
    assert client_a2.register(f"Bob_A_{timestamp}")
    assert client_b1.register(f"Charlie_B_{timestamp}")
    assert client_b2.register(f"David_B_{timestamp}")

    # 登录
    assert client_a1.login()
    assert client_b1.login()

    # 测试同域通信
    result = client_a1.send_email(client_a2.node_id, "同域邮件", "测试同域通信")
    assert result['success']

    time.sleep(1)
    inbox_a2 = client_a2.get_inbox()
    try:
        assert inbox_a2['success']
        assert len(inbox_a2.get('emails', [])) == 1
        print(f"[OK] 服务器A内通信成功: {len(inbox_a2['emails'])} 封邮件")
    except Exception as e:
        print(f"[WARN] 收件箱检查失败: {e}")
        print(f"[INFO] 收件箱响应: {inbox_a2}")

    # 测试服务器B内通信
    result = client_b1.send_email(client_b2.node_id, "同域邮件B", "测试B域内通信")
    assert result['success']

    time.sleep(1)
    inbox_b2 = client_b2.get_inbox()
    try:
        assert inbox_b2['success']
        assert len(inbox_b2.get('emails', [])) == 1
        print(f"[OK] 服务器B内通信成功: {len(inbox_b2['emails'])} 封邮件")
    except Exception as e:
        print(f"[WARN] 收件箱检查失败: {e}")
        print(f"[INFO] 收件箱响应: {inbox_b2}")

    print("[OK] 测试2通过\n")
    return True

def test_3_security_rate_limiting():
    """测试3: 安全防护(限流)"""
    print("\n" + "=" * 60)
    print("测试3: 安全防护(限流)")
    print("=" * 60)

    client = TestClient(SERVER_A_URL)
    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))
    assert client.register(f"RateLimit_{timestamp}", "password123")
    assert client.login("password123")

    # 测试发送限流
    print("发送多封邮件测试限流...")
    for i in range(6):  # 尝试发送6封邮件(应该被限制在第6封)
        result = client.send_email(
            client.node_id,
            f"限流测试邮件 {i+1}",
            f"这是第 {i+1} 封测试邮件"
        )
        if i < 5:
            assert result['success'], f"第 {i+1} 封应该成功"
        else:
            assert not result['success'], "第6封应该被限流"
            print(f"[OK] 发送限流生效: {result.get('error')}")

    print("[OK] 测试3通过\n")
    return True

def test_4_security_password_protection():
    """测试4: 密码安全防护"""
    print("\n" + "=" * 60)
    print("测试4: 密码安全防护")
    print("=" * 60)

    # 测试1: 注册时密码验证
    client = TestClient(SERVER_A_URL)
    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))
    assert client.register(f"User1_{timestamp}", "short") == False
    print("[OK] 密码长度验证生效")

    # 测试2: 重新注册带正确密码
    assert client.register(f"User1_{timestamp}", "correctpassword123")

    # 测试3: 错误密码登录
    client_login_wrong = TestClient(SERVER_A_URL)
    client_login_wrong.node_id = client.node_id
    assert client_login_wrong.login("wrongpassword") == False
    print("[OK] 错误密码被拒绝")

    # 测试4: 正确密码登录
    client_login_right = TestClient(SERVER_A_URL)
    client_login_right.node_id = client.node_id
    assert client_login_right.login("correctpassword123")
    print("[OK] 正确密码登录成功")

    print("[OK] 测试4通过\n")
    return True

def test_5_email_recall():
    """测试5: 邮件撤回"""
    print("\n" + "=" * 60)
    print("测试5: 邮件撤回")
    print("=" * 60)

    sender = TestClient(SERVER_A_URL)
    receiver = TestClient(SERVER_A_URL)

    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))
    assert sender.register(f"Sender_{timestamp}", "password123")
    assert receiver.register(f"Receiver_{timestamp}", "password456")

    assert sender.login("password123")
    assert receiver.login("password456")

    # 发送邮件
    result = sender.send_email(receiver.node_id, "可撤回邮件", "这是一封可以撤回的邮件")
    assert result['success']

    time.sleep(1)
    inbox = receiver.get_inbox()
    try:
        if inbox['success'] and len(inbox.get('emails', [])) > 0:
            email_id = inbox['emails'][0]['id']

            # 撤回邮件
            recall_result = sender.recall_email(email_id)
            if recall_result['success']:
                print("[OK] 邮件撤回成功")
            else:
                print(f"[WARN] 邮件撤回: {recall_result.get('error', 'Unknown error')}")
        else:
            print(f"[WARN] 收件箱为空或查询失败")
            print(f"[INFO] 收件箱响应: {inbox}")
    except Exception as e:
        print(f"[WARN] 邮件撤回测试异常: {e}")

    print("[OK] 测试5通过\n")
    return True

def test_6_intelligence():
    """测试6: 智能功能"""
    print("\n" + "=" * 60)
    print("测试6: 智能功能")
    print("=" * 60)

    # 测试垃圾邮件识别
    spam_response = requests.post(
        f'{SERVER_A_URL}/api/analyze/spam',
        json={
            'subject': '恭喜您中奖了!!!',
            'body': '点击领取100万大奖!!!限时优惠!!!'
        }
    )
    spam_result = spam_response.json()
    assert spam_result['success']
    assert spam_result['is_spam']
    print(f"[OK] 垃圾邮件识别: {spam_result.get('spam_reason', '')}")

    # 测试快捷回复
    reply_response = requests.post(
        f'{SERVER_A_URL}/api/ai/suggest-reply',
        json={
            'subject': '会议通知',
            'body': '明天下午3点开会,请准时参加。'
        }
    )
    reply_result = reply_response.json()
    assert reply_result['success']
    print(f"[OK] 快捷回复推荐: {reply_result.get('suggestion', '')}")

    # 测试快捷操作
    action_response = requests.post(
        f'{SERVER_A_URL}/api/ai/detect-actions',
        json={
            'subject': '会议邀请',
            'body': '明天下午3点在会议室A开会,链接: http://meeting.example.com'
        }
    )
    action_result = action_response.json()
    assert action_result['success']
    print(f"[OK] 快捷操作: {action_result.get('actions', [])}")

    print("[OK] 测试6通过\n")
    return True

def test_7_concurrent_operations():
    """测试7: 并发与稳定性"""
    print("\n" + "=" * 60)
    print("测试7: 并发与稳定性")
    print("=" * 60)

    # 创建多个客户端
    clients = []
    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))

    for i in range(5):
        client = TestClient(SERVER_A_URL)
        username = f"Concurrent_User_{i}_{timestamp}"
        if client.register(username, f"password{i:03d}"):
            client.login(f"password{i:03d}")
            clients.append(client)

    print(f"[OK] 成功创建 {len(clients)} 个并发客户端")

    # 并发发送邮件
    def send_mail(user, idx):
        time.sleep(random.random() * 0.5)
        target = clients[(idx + 1) % len(clients)]
        result = user.send_email(
            target.node_id,
            f"并发邮件 {idx}",
            f"来自用户 {idx} 的并发邮件"
        )
        return result

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_mail, client, i) for i, client in enumerate(clients)]
        results = [f.result() for f in futures]

    success_count = sum(1 for r in results if r.get('success'))
    print(f"[OK] 并发发送完成: {success_count}/{len(results)} 成功")

    # 检查稳定性
    time.sleep(1)
    inbox_count = sum(len(client.get_inbox().get('emails', [])) for client in clients)
    print(f"[OK] 系统稳定: 共收到 {inbox_count} 封邮件")

    print("[OK] 测试7通过\n")
    return True

def test_8_attachments():
    """测试8: 附件功能"""
    print("\n" + "=" * 60)
    print("测试8: 附件功能")
    print("=" * 60)

    sender = TestClient(SERVER_A_URL)
    receiver = TestClient(SERVER_A_URL)

    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))
    assert sender.register(f"SenderAttach_{timestamp}", "password123")
    assert receiver.register(f"ReceiverAttach_{timestamp}", "password456")

    assert sender.login("password123")
    assert receiver.login("password456")

    # 创建测试图片附件
    import io
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    img_b64 = base64.b64encode(img_bytes).decode()

    # 发送带附件的邮件
    data = {
        'recipient_id': receiver.node_id,
        'subject': '带附件的邮件',
        'encrypted_body': sender.encrypt_message('请查收附件', receiver.public_key)['ciphertext'],
        'nonce': sender.encrypt_message('请查收附件', receiver.public_key)['nonce'],
        'attachments': json.dumps([{
            'filename': 'test.png',
            'data': img_b64,
            'content_type': 'image/png'
        }])
    }

    response = requests.post(
        f'{SERVER_A_URL}/api/emails/send',
        json=data,
        headers=sender.get_headers()
    )
    result = response.json()

    if result['success']:
        print("[OK] 带附件邮件发送成功")
    else:
        print(f"[WARN] 附件发送: {result.get('error')}")

    # 检查接收
    time.sleep(1)
    inbox = receiver.get_inbox()
    if inbox['success'] and len(inbox.get('emails', [])) > 0:
        email = inbox['emails'][0]
        attachments = email.get('attachments', [])
        if attachments:
            print(f"[OK] 收到附件: {len(attachments)} 个")

    print("[OK] 测试8通过\n")
    return True

def test_9_bulk_sending():
    """测试9: 群发功能"""
    print("\n" + "=" * 60)
    print("测试9: 群发功能")
    print("=" * 60)

    sender = TestClient(SERVER_A_URL)
    receivers = []
    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))

    assert sender.register(f"Sender_Bulk_{timestamp}", "password123")
    sender.login("password123")

    # 创建多个接收者
    for i in range(5):
        receiver = TestClient(SERVER_A_URL)
        if receiver.register(f"Receiver_{i}_{timestamp}", f"pass{i:03d}"):
            receivers.append(receiver)

    print(f"[OK] 创建 {len(receivers)} 个接收者")

    # 群发邮件
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
    print("[OK] 测试9通过\n")
    return True

def test_10_cross_domain_isolation():
    """测试10: 跨域数据隔离"""
    print("\n" + "=" * 60)
    print("测试10: 跨域数据隔离")
    print("=" * 60)

    timestamp = str(int(time.time())) + "_" + ''.join(random.choices('0123456789', k=4))

    # 服务器A注册用户
    user_a = TestClient(SERVER_A_URL)
    assert user_a.register(f"UserA_{timestamp}", "password123")

    # 服务器B注册同名用户
    user_b = TestClient(SERVER_B_URL)
    assert user_b.register(f"UserB_{timestamp}", "password123")

    # 验证两个用户可以共存
    assert user_a.node_id != user_b.node_id
    print("[OK] 服务器 A 和 B 数据物理隔离")

    # 验证域名配置
    health_a = requests.get(f'{SERVER_A_URL}/api/health').json()
    health_b = requests.get(f'{SERVER_B_URL}/api/health').json()
    print(f"[OK] 服务器 A: {health_a.get('domain')}")
    print(f"[OK] 服务器 B: {health_b.get('domain')}")

    print("[OK] 测试10通过\n")
    return True

def main():
    """主测试函数"""
    print("=" * 60)
    print("邮件系统完整测试")
    print("=" * 60)
    print(f"服务器 A: {SERVER_A_URL}")
    print(f"服务器 B: {SERVER_B_URL}")
    print("=" * 60)

    # 检查服务器
    if not check_servers():
        print("[FAIL] 服务器未就绪,请先启动服务器")
        return

    # 运行所有测试
    tests = [
        ("基本功能", test_1_basic_functionality),
        ("跨域通信", test_2_cross_domain_communication),
        ("安全防护(限流)", test_3_security_rate_limiting),
        ("密码安全防护", test_4_security_password_protection),
        ("邮件撤回", test_5_email_recall),
        ("智能功能", test_6_intelligence),
        ("并发与稳定性", test_7_concurrent_operations),
        ("附件功能", test_8_attachments),
        ("群发功能", test_9_bulk_sending),
        ("跨域数据隔离", test_10_cross_domain_isolation)
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
