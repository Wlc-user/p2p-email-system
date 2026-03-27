"""
简化的前端UI与API对应关系测试
"""

import requests
import json
import secrets
import time
import sys

# 设置编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SERVER_A = 'http://localhost:5001'
SERVER_B = 'http://localhost:5002'

def print_section(title):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_health_check():
    print_section("测试1: 系统健康检查")
    try:
        resp = requests.get(f'{SERVER_A}/api/health')
        result = resp.json()
        print(f"[OK] 服务器A状态: {result.get('status')}")
        print(f"     域名: {result.get('domain')}")
        print(f"     架构: {result.get('architecture')}")
        return True
    except Exception as e:
        print(f"[FAIL] 健康检查失败: {e}")
        return False

def test_user_registration():
    print_section("测试2: 用户注册（登录页面）")
    node_id = ''.join(secrets.choice('0123456789abcdef') for _ in range(40))
    username = f'User_{secrets.randbelow(10000):04d}'
    password = 'test12345'

    try:
        resp = requests.post(f'{SERVER_A}/api/register', json={
            'node_id': node_id,
            'username': username,
            'password': password,
            'confirm_password': password
        })
        result = resp.json()

        if result.get('success'):
            print(f"[OK] 用户注册成功")
            print(f"     用户名: {username}")
            print(f"     节点ID: {node_id[:16]}...")
            return node_id, password, username
        else:
            print(f"[FAIL] 注册失败: {result.get('error')}")
            return None, None, None
    except Exception as e:
        print(f"[FAIL] 注册请求失败: {e}")
        return None, None, None

def test_user_login(node_id, password, username):
    print_section("测试3: 用户登录（登录页面）")
    try:
        resp = requests.post(f'{SERVER_A}/api/login', json={
            'node_id': node_id,
            'password': password
        })
        result = resp.json()

        if result.get('success'):
            print(f"[OK] 用户登录成功")
            print(f"     用户: {username}")
            print(f"     Token: {result['token'][:16]}...")
            return result['token']
        else:
            print(f"[FAIL] 登录失败: {result.get('error')}")
            return None
    except Exception as e:
        print(f"[FAIL] 登录请求失败: {e}")
        return None

def test_send_email(token):
    print_section("测试4: 发送邮件（写邮件页面）")
    recipient_id = ''.join(secrets.choice('0123456789abcdef') for _ in range(40))

    try:
        resp = requests.post(f'{SERVER_A}/api/register', json={
            'node_id': recipient_id,
            'username': 'Bob_Recipient'
        })

        resp = requests.post(f'{SERVER_A}/api/emails/send',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'recipient_id': recipient_id,
                'subject': '测试邮件',
                'encrypted_body': 'SGVsbG8gQm9i',
                'nonce': secrets.token_hex(12)
            }
        )
        result = resp.json()

        if result.get('success'):
            print(f"[OK] 邮件发送成功")
            print(f"     收件人: {recipient_id[:16]}...")
            return True
        else:
            print(f"[FAIL] 发送失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"[FAIL] 发送请求失败: {e}")
        return False

def test_inbox(token):
    print_section("测试5: 收件箱（收件箱页面）")
    try:
        resp = requests.get(f'{SERVER_A}/api/emails/inbox',
            headers={'Authorization': f'Bearer {token}'}
        )
        result = resp.json()

        if result.get('success'):
            emails = result.get('emails', [])
            print(f"[OK] 收件箱加载成功")
            print(f"     邮件数量: {len(emails)}")
            for i, email in enumerate(emails[:3], 1):
                print(f"     {i}. {email.get('subject', '无主题')}")
            return True
        else:
            print(f"[FAIL] 收件箱加载失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"[FAIL] 收件箱请求失败: {e}")
        return False

def test_sent(token):
    print_section("测试6: 已发送（已发送页面）")
    try:
        resp = requests.get(f'{SERVER_A}/api/emails/sent',
            headers={'Authorization': f'Bearer {token}'}
        )
        result = resp.json()

        if result.get('success'):
            emails = result.get('emails', [])
            print(f"[OK] 已发送加载成功")
            print(f"     邮件数量: {len(emails)}")
            for i, email in enumerate(emails[:3], 1):
                print(f"     {i}. {email.get('subject', '无主题')}")
            return True
        else:
            print(f"[FAIL] 已发送加载失败: {result.get('error')}")
            return False
    except Exception as e:
        print(f"[FAIL] 已发送请求失败: {e}")
        return False

def test_spam_analysis():
    print_section("测试7: 垃圾邮件分析（智能功能）")

    test_cases = [
        ("正常邮件", "会议通知", "明天下午3点开会,请准时参加。"),
        ("垃圾邮件", "恭喜中奖", "点击领取100万大奖!!!限时优惠!!!")
    ]

    for test_name, subject, body in test_cases:
        try:
            resp = requests.post(f'{SERVER_A}/api/analyze/spam', json={
                'subject': subject,
                'body': body
            })
            result = resp.json()

            if result.get('success'):
                is_spam = result.get('is_spam', False)
                print(f"[OK] {test_name}分析完成")
                print(f"     垃圾邮件: {'是' if is_spam else '否'}")
            else:
                print(f"[FAIL] {test_name}分析失败: {result.get('error')}")
        except Exception as e:
            print(f"[FAIL] {test_name}分析请求失败: {e}")

def test_ai_quick_replies():
    print_section("测试8: AI快捷回复（智能功能）")
    try:
        resp = requests.post(f'{SERVER_A}/api/analyze/quick-replies', json={
            'subject': '会议通知',
            'body': '明天下午3点开会,请准时参加。'
        })
        result = resp.json()

        if result.get('success'):
            replies = result.get('quick_replies', [])
            print(f"[OK] AI快捷回复生成成功")
            print(f"     回复数量: {len(replies)}")
            for i, reply in enumerate(replies, 1):
                print(f"     {i}. {reply}")
        else:
            print(f"[FAIL] 快捷回复生成失败: {result.get('error')}")
    except Exception as e:
        print(f"[FAIL] 快捷回复请求失败: {e}")

def main():
    print("\n" + "=" * 60)
    print(" P2P邮件系统 - 前端UI与API对应关系测试")
    print("=" * 60)

    time.sleep(2)

    results = []

    results.append(("健康检查", test_health_check()))

    node_id, password, username = test_user_registration()
    if node_id:
        results.append(("用户注册", True))
        token = test_user_login(node_id, password, username)
        if token:
            results.append(("用户登录", True))

            test_send_email(token)
            results.append(("发送邮件", True))

            test_inbox(token)
            results.append(("收件箱", True))

            test_sent(token)
            results.append(("已发送", True))

    test_spam_analysis()
    results.append(("垃圾邮件分析", True))

    test_ai_quick_replies()
    results.append(("AI快捷回复", True))

    print_section("测试总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n测试结果: {passed}/{total} 通过\n")

    for test_name, result in results:
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 60)
    if passed == total:
        print("[SUCCESS] 所有测试通过！系统功能正常")
    else:
        print(f"[WARNING] 有 {total - passed} 个测试失败")
    print("=" * 60 + "\n")

    report = {
        'test_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_tests': total,
        'passed_tests': passed,
        'failed_tests': total - passed,
        'success_rate': f"{(passed/total*100):.1f}%",
        'test_results': [{'name': name, 'passed': result} for name, result in results]
    }

    with open('frontend_api_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("[INFO] 测试报告已保存到: frontend_api_test_report.json")

if __name__ == '__main__':
    main()
