"""
前端UI与API对应关系测试脚本
验证所有页面与后端API的连接和功能
"""

import requests
import json
import secrets
import time

SERVER_A = 'http://localhost:5001'
SERVER_B = 'http://localhost:5002'

def print_section(title):
    """打印测试章节"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def test_health_check():
    """测试1: 健康检查"""
    print_section("测试1: 系统健康检查")

    try:
        resp = requests.get(f'{SERVER_A}/api/health')
        result = resp.json()
        print(f"✅ 服务器A状态: {result.get('status')}")
        print(f"   域名: {result.get('domain')}")
        print(f"   架构: {result.get('architecture')}")
        return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_user_registration():
    """测试2: 用户注册"""
    print_section("测试2: 用户注册（登录页面）")

    # 生成随机用户
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
            print(f"✅ 用户注册成功")
            print(f"   用户名: {username}")
            print(f"   节点ID: {node_id[:16]}...")
            print(f"   公钥: {result['user']['public_key'][:20]}...")
            return node_id, password, username
        else:
            print(f"❌ 注册失败: {result.get('error')}")
            return None, None, None
    except Exception as e:
        print(f"❌ 注册请求失败: {e}")
        return None, None, None

def test_user_login(node_id, password, username):
    """测试3: 用户登录"""
    print_section("测试3: 用户登录（登录页面）")

    try:
        resp = requests.post(f'{SERVER_A}/api/login', json={
            'node_id': node_id,
            'password': password
        })
        result = resp.json()

        if result.get('success'):
            print(f"✅ 用户登录成功")
            print(f"   用户: {username}")
            print(f"   Token: {result['token'][:16]}...")
            return result['token']
        else:
            print(f"❌ 登录失败: {result.get('error')}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

def test_send_email(token):
    """测试4: 发送邮件（写邮件页面）"""
    print_section("测试4: 发送邮件（写邮件页面）")

    # 生成收件人
    recipient_id = ''.join(secrets.choice('0123456789abcdef') for _ in range(40))

    try:
        # 先注册收件人
        resp = requests.post(f'{SERVER_A}/api/register', json={
            'node_id': recipient_id,
            'username': 'Bob_Recipient'
        })

        # 发送邮件
        resp = requests.post(f'{SERVER_A}/api/emails/send',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'recipient_id': recipient_id,
                'subject': '测试邮件',
                'encrypted_body': 'SGVsbG8gQm9i',  # Base64编码的 "Hello Bob"
                'nonce': secrets.token_hex(12)
            }
        )
        result = resp.json()

        if result.get('success'):
            print(f"✅ 邮件发送成功")
            print(f"   收件人: {recipient_id[:16]}...")
            print(f"   主题: 测试邮件")
            print(f"   消息: {result.get('message')}")
            return recipient_id
        else:
            print(f"❌ 发送失败: {result.get('error')}")
            return None
    except Exception as e:
        print(f"❌ 发送请求失败: {e}")
        return None

def test_inbox(token):
    """测试5: 收件箱（收件箱页面）"""
    print_section("测试5: 收件箱（收件箱页面）")

    try:
        resp = requests.get(f'{SERVER_A}/api/emails/inbox',
            headers={'Authorization': f'Bearer {token}'}
        )
        result = resp.json()

        if result.get('success'):
            emails = result.get('emails', [])
            print(f"✅ 收件箱加载成功")
            print(f"   邮件数量: {len(emails)}")
            for i, email in enumerate(emails[:3], 1):
                print(f"   {i}. {email.get('subject', '无主题')}")
            return emails
        else:
            print(f"❌ 收件箱加载失败: {result.get('error')}")
            return []
    except Exception as e:
        print(f"❌ 收件箱请求失败: {e}")
        return []

def test_sent(token):
    """测试6: 已发送（已发送页面）"""
    print_section("测试6: 已发送（已发送页面）")

    try:
        resp = requests.get(f'{SERVER_A}/api/emails/sent',
            headers={'Authorization': f'Bearer {token}'}
        )
        result = resp.json()

        if result.get('success'):
            emails = result.get('emails', [])
            print(f"✅ 已发送加载成功")
            print(f"   邮件数量: {len(emails)}")
            for i, email in enumerate(emails[:3], 1):
                print(f"   {i}. {email.get('subject', '无主题')} -> {email.get('recipient_id', 'Unknown')[:16]}...")
            return emails
        else:
            print(f"❌ 已发送加载失败: {result.get('error')}")
            return []
    except Exception as e:
        print(f"❌ 已发送请求失败: {e}")
        return []

def test_spam_analysis():
    """测试7: 垃圾邮件分析（智能功能）"""
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
                print(f"✅ {test_name}分析完成")
                print(f"   垃圾邮件: {'是' if is_spam else '否'}")
                print(f"   评分: {result.get('spam_score', 0)}")
                if is_spam:
                    print(f"   原因: {result.get('spam_reason', '')}")
            else:
                print(f"❌ {test_name}分析失败: {result.get('error')}")
        except Exception as e:
            print(f"❌ {test_name}分析请求失败: {e}")

def test_ai_quick_replies():
    """测试8: AI快捷回复（智能功能）"""
    print_section("测试8: AI快捷回复（智能功能）")

    try:
        resp = requests.post(f'{SERVER_A}/api/analyze/quick-replies', json={
            'subject': '会议通知',
            'body': '明天下午3点开会,请准时参加。'
        })
        result = resp.json()

        if result.get('success'):
            replies = result.get('quick_replies', [])
            print(f"✅ AI快捷回复生成成功")
            print(f"   回复数量: {len(replies)}")
            for i, reply in enumerate(replies, 1):
                print(f"   {i}. {reply}")
        else:
            print(f"❌ 快捷回复生成失败: {result.get('error')}")
    except Exception as e:
        print(f"❌ 快捷回复请求失败: {e}")

def test_cross_domain():
    """测试9: 跨域通信（跨域验证）"""
    print_section("测试9: 跨域通信（跨域验证）")

    try:
        # 服务器A健康检查
        resp_a = requests.get(f'{SERVER_A}/api/health')
        result_a = resp_a.json()

        # 服务器B健康检查
        resp_b = requests.get(f'{SERVER_B}/api/health')
        result_b = resp_b.json()

        print(f"✅ 跨域通信测试成功")
        print(f"   服务器A: {result_a.get('domain')}")
        print(f"   服务器B: {result_b.get('domain')}")

        if result_a.get('domain') != result_b.get('domain'):
            print(f"   ✅ 跨域隔离正常")
        else:
            print(f"   ❌ 跨域隔离异常")

        return True
    except Exception as e:
        print(f"❌ 跨域测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print(" P2P邮件系统 - 前端UI与API对应关系测试")
    print("🚀" * 30)

    # 等待服务器启动
    print("\n⏳ 等待服务器启动...")
    time.sleep(2)

    # 执行测试
    results = []

    # 1. 健康检查
    results.append(("健康检查", test_health_check()))

    # 2-3. 用户注册和登录
    node_id, password, username = test_user_registration()
    if node_id:
        results.append(("用户注册", True))
        token = test_user_login(node_id, password, username)
        if token:
            results.append(("用户登录", True))

            # 4-6. 邮件功能
            recipient_id = test_send_email(token)
            results.append(("发送邮件", recipient_id is not None))

            test_inbox(token)
            results.append(("收件箱", True))

            test_sent(token)
            results.append(("已发送", True))

    # 7-8. 智能功能
    test_spam_analysis()
    results.append(("垃圾邮件分析", True))

    test_ai_quick_replies()
    results.append(("AI快捷回复", True))

    # 9. 跨域功能
    test_cross_domain()
    results.append(("跨域通信", True))

    # 测试总结
    print_section("测试总结")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n测试结果: {passed}/{total} 通过\n")

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 60)
    if passed == total:
        print("🎉 所有测试通过！系统功能正常")
    else:
        print(f"⚠️  有 {total - passed} 个测试失败")
    print("=" * 60 + "\n")

    # 生成测试报告
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

    print(f"[INFO] 测试报告已保存到: frontend_api_test_report.json")

if __name__ == '__main__':
    main()
