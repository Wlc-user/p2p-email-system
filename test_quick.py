"""
快速测试脚本 - 验证核心功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import time
import secrets

SERVER_A = 'http://localhost:5001'
SERVER_B = 'http://localhost:5002'

def test_basic():
    """基本功能测试"""
    print("\n=== 测试1: 基本功能 ===")

    # 注册用户
    import random
    node_id_a = ''.join(random.choices('0123456789abcdef', k=40))
    resp = requests.post(f'{SERVER_A}/api/register', json={
        'node_id': node_id_a,
        'username': f'Alice_{random.randint(1000, 9999)}',
        'password': 'alice123',
        'confirm_password': 'alice123'
    })
    assert resp.json()['success'], f"注册失败: {resp.text}"
    print(f"[OK] Alice注册成功")

    node_id_b = ''.join(random.choices('0123456789abcdef', k=40))
    resp = requests.post(f'{SERVER_A}/api/register', json={
        'node_id': node_id_b,
        'username': f'Bob_{random.randint(1000, 9999)}',
        'password': 'bob12345',
        'confirm_password': 'bob12345'
    })
    assert resp.json()['success'], f"注册失败: {resp.text}"
    print(f"[OK] Bob注册成功")

    # 登录
    resp = requests.post(f'{SERVER_A}/api/login', json={'node_id': node_id_a, 'password': 'alice123'})
    token_a = resp.json()['token']
    print(f"[OK] Alice登录成功")

    # 发送邮件
    resp = requests.get(f'{SERVER_A}/api/publickey/{node_id_b}')
    pubkey_b = resp.json()['public_key']

    from cryptography.hazmat.primitives.asymmetric import x25519
    from cryptography.hazmat.primitives import serialization
    import hashlib
    import base64
    import os
    from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

    # 生成密钥对
    private_key = x25519.X25519PrivateKey.generate()
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # 简化:直接发送未加密邮件(为了快速测试)
    resp = requests.post(f'{SERVER_A}/api/emails/send',
        headers={'Authorization': f'Bearer {token_a}', 'Content-Type': 'application/json'},
        json={
            'recipient_id': node_id_b,
            'subject': '测试邮件',
            'encrypted_body': base64.b64encode(b'Hello Bob').decode(),
            'nonce': base64.b64encode(os.urandom(12)).decode()
        }
    )
    print(f"[OK] 发送邮件")

    # 检查收件箱
    resp = requests.post(f'{SERVER_A}/api/login', json={'node_id': node_id_b, 'password': 'bob12345'})
    resp_data = resp.json()
    assert resp_data['success'], f"Bob登录失败: {resp_data.get('error')}"
    token_b = resp_data['token']

    resp = requests.get(f'{SERVER_A}/api/emails/inbox',
        headers={'Authorization': f'Bearer {token_b}'}
    )
    inbox = resp.json()
    assert inbox['success'], f"获取收件箱失败: {inbox.get('error')}"
    assert len(inbox.get('emails', [])) > 0, "收件箱为空"
    print(f"[OK] Bob收到邮件: {len(inbox['emails'])}封")

    return True

def test_cross_domain():
    """跨域测试"""
    print("\n=== 测试2: 跨域通信 ===")

    # 服务器A注册
    import random
    node_id_a = ''.join(random.choices('0123456789abcdef', k=40))
    resp = requests.post(f'{SERVER_A}/api/register', json={
        'node_id': node_id_a,
        'username': f'UserA_{random.randint(1000, 9999)}'
    })
    assert resp.json()['success']
    print(f"[OK] 服务器A用户注册成功")

    # 服务器B注册
    node_id_b = ''.join(random.choices('0123456789abcdef', k=40))
    resp = requests.post(f'{SERVER_B}/api/register', json={
        'node_id': node_id_b,
        'username': f'UserB_{random.randint(1000, 9999)}'
    })
    assert resp.json()['success']
    print(f"[OK] 服务器B用户注册成功")

    # 验证隔离
    health_a = requests.get(f'{SERVER_A}/api/health').json()
    health_b = requests.get(f'{SERVER_B}/api/health').json()

    assert health_a['domain'] == 'mail-a.com'
    assert health_b['domain'] == 'mail-b.com'
    print(f"[OK] 跨域隔离验证: {health_a['domain']} vs {health_b['domain']}")

    return True

def test_spam_detection():
    """垃圾邮件识别"""
    print("\n=== 测试3: 垃圾邮件识别 ===")

    resp = requests.post(f'{SERVER_A}/api/analyze/spam', json={
        'subject': '恭喜中奖!!!',
        'body': '点击领取100万大奖!!!限时优惠!!!'
    })
    result = resp.json()

    assert result['success'], f"分析失败: {result.get('error')}"
    assert result['is_spam'], "应该是垃圾邮件"
    print(f"[OK] 垃圾邮件识别成功: {result.get('spam_reason', '')}")

    return True

def test_ai_reply():
    """AI快捷回复"""
    print("\n=== 测试4: AI快捷回复 ===")

    resp = requests.post(f'{SERVER_A}/api/analyze/quick-replies', json={
        'subject': '会议通知',
        'body': '明天下午3点开会,请准时参加。'
    })
    result = resp.json()

    assert result['success'], f"回复失败: {result.get('error')}"
    print(f"[OK] 快捷回复: {result.get('quick_replies', '')}")

    return True

def main():
    print("=" * 60)
    print("邮箱系统快速测试")
    print("=" * 60)

    tests = [
        ("基本功能", test_basic),
        ("跨域通信", test_cross_domain),
        ("垃圾邮件识别", test_spam_detection),
        ("AI快捷回复", test_ai_reply)
    ]

    passed = 0
    for name, test in tests:
        try:
            test()
            passed += 1
            print(f"[OK] {name}通过")
        except Exception as e:
            print(f"[FAIL] {name}失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{len(tests)} 通过")
    print("=" * 60)

if __name__ == '__main__':
    main()
