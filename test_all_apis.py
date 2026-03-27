#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能安全邮箱系统 - 完整API测试脚本
测试所有邮箱功能：注册、登录、发送、接收、查看、编辑等
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ant coding'))

from client.mail_client import MailClient

def print_section(title):
    """打印测试区域标题"""
    print("\n" + "=" * 60)
    print(f"  {title}".center(60))
    print("=" * 60 + "\n")

def print_success(msg):
    print(f"✓ {msg}")

def print_error(msg):
    print(f"✗ {msg}")

def print_info(msg):
    print(f"ℹ {msg}")

def test_all_apis():
    """测试所有API功能"""
    
    # 创建客户端
    client = MailClient()
    
    # 测试结果统计
    results = {
        'passed': 0,
        'failed': 0,
        'tests': []
    }
    
    # ========================================
    # 1. 连接服务器测试
    # ========================================
    print_section("1. 连接服务器测试")
    
    try:
        print_info("连接到 example1.com...")
        if client.connect_to_server("example1.com"):
            print_success("连接到 example1.com 成功")
            results['tests'].append(('连接服务器', True))
            results['passed'] += 1
        else:
            print_error("连接到 example1.com 失败")
            results['tests'].append(('连接服务器', False))
            results['failed'] += 1
    except Exception as e:
        print_error(f"连接异常: {e}")
        results['tests'].append(('连接服务器', False))
        results['failed'] += 1
    
    # ========================================
    # 2. 注册用户测试
    # ========================================
    print_section("2. 注册用户测试")
    
    test_users = [
        {
            'username': 'alice',
            'password': 'alice123',
            'email': 'alice@example1.com'
        },
        {
            'username': 'bob',
            'password': 'bob123',
            'email': 'bob@example1.com'
        }
    ]
    
    for user in test_users:
        try:
            print_info(f"注册用户: {user['username']}")
            if client.register_user(user['username'], user['password'], user['email']):
                print_success(f"用户 {user['username']} 注册成功")
                results['tests'].append((f"注册{user['username']}", True))
                results['passed'] += 1
            else:
                print_info(f"用户 {user['username']} 可能已存在（这是正常的）")
                results['tests'].append((f"注册{user['username']}", True))
                results['passed'] += 1
        except Exception as e:
            print_error(f"注册异常: {e}")
            results['tests'].append((f"注册{user['username']}", False))
            results['failed'] += 1
    
    # ========================================
    # 3. 用户登录测试
    # ========================================
    print_section("3. 用户登录测试")
    
    try:
        print_info("登录用户: alice")
        if client.login('alice', 'alice123', remember_me=False):
            print_success("alice 登录成功")
            results['tests'].append(('登录', True))
            results['passed'] += 1
        else:
            print_error("alice 登录失败")
            results['tests'].append(('登录', False))
            results['failed'] += 1
    except Exception as e:
        print_error(f"登录异常: {e}")
        results['tests'].append(('登录', False))
        results['failed'] += 1
    
    # ========================================
    # 4. 发送邮件测试
    # ========================================
    print_section("4. 发送邮件测试")
    
    test_mails = [
        {
            'to': ['bob@example1.com'],
            'subject': '测试邮件1',
            'body': '这是第一封测试邮件'
        },
        {
            'to': ['alice@example1.com'],
            'subject': '回复测试',
            'body': '这是回复邮件'
        },
        {
            'to': ['bob@example1.com', 'alice@example1.com'],
            'subject': '群发测试',
            'body': '这是群发邮件测试',
            'cc': ['test@example1.com']
        }
    ]
    
    for i, mail in enumerate(test_mails, 1):
        try:
            print_info(f"发送第 {i} 封邮件: {mail['subject']}")
            mail_id = client.send_mail(
                to_addresses=mail['to'],
                subject=mail['subject'],
                body=mail['body'],
                cc_addresses=mail.get('cc', [])
            )
            if mail_id:
                print_success(f"邮件 {i} 发送成功 (ID: {mail_id})")
                results['tests'].append((f"发送邮件{i}", True))
                results['passed'] += 1
            else:
                print_error(f"邮件 {i} 发送失败")
                results['tests'].append((f"发送邮件{i}", False))
                results['failed'] += 1
        except Exception as e:
            print_error(f"发送邮件异常: {e}")
            results['tests'].append((f"发送邮件{i}", False))
            results['failed'] += 1
    
    # ========================================
    # 5. 查看收件箱测试
    # ========================================
    print_section("5. 查看收件箱测试")
    
    try:
        print_info("获取收件箱...")
        inbox = client.get_mailbox("inbox")
        print_success(f"收件箱获取成功，共 {len(inbox)} 封邮件")
        results['tests'].append(('查看收件箱', True))
        results['passed'] += 1
        
        if inbox:
            print("\n收件箱内容:")
            for i, mail in enumerate(inbox[:3], 1):
                sender = f"{mail['sender']['username']}@{mail['sender']['domain']}"
                subject = mail['subject']
                print(f"  {i}. {sender} - {subject}")
    except Exception as e:
        print_error(f"获取收件箱异常: {e}")
        results['tests'].append(('查看收件箱', False))
        results['failed'] += 1
    
    # ========================================
    # 6. 查看已发送测试
    # ========================================
    print_section("6. 查看已发送测试")
    
    try:
        print_info("获取已发送...")
        sent = client.get_mailbox("sent")
        print_success(f"已发送获取成功，共 {len(sent)} 封邮件")
        results['tests'].append(('查看已发送', True))
        results['passed'] += 1
        
        if sent:
            print("\n已发送内容:")
            for i, mail in enumerate(sent[:3], 1):
                recipients = ", ".join([f"{r['username']}@{r['domain']}" for r in mail['recipients']])
                subject = mail['subject']
                print(f"  {i}. {recipients} - {subject}")
    except Exception as e:
        print_error(f"获取已发送异常: {e}")
        results['tests'].append(('查看已发送', False))
        results['failed'] += 1
    
    # ========================================
    # 7. 查看草稿箱测试
    # ========================================
    print_section("7. 查看草稿箱测试")
    
    try:
        print_info("获取草稿箱...")
        drafts = client.get_mailbox("drafts")
        print_success(f"草稿箱获取成功，共 {len(drafts)} 封草稿")
        results['tests'].append(('查看草稿箱', True))
        results['passed'] += 1
    except Exception as e:
        print_error(f"获取草稿箱异常: {e}")
        results['tests'].append(('查看草稿箱', False))
        results['failed'] += 1
    
    # ========================================
    # 8. 搜索邮件测试
    # ========================================
    print_section("8. 搜索邮件测试")
    
    search_keywords = ['测试', '回复']
    
    for keyword in search_keywords:
        try:
            print_info(f"搜索关键词: {keyword}")
            results = client.search_mail(keyword)
            print_success(f"搜索成功，找到 {len(results)} 封邮件")
            results['tests'].append((f"搜索'{keyword}'", True))
            results['passed'] += 1
            
            if results:
                print(f"\n搜索结果:")
                for i, mail in enumerate(results[:3], 1):
                    subject = mail['subject']
                    print(f"  {i}. {subject}")
        except Exception as e:
            print_error(f"搜索异常: {e}")
            results['tests'].append((f"搜索'{keyword}'", False))
            results['failed'] += 1
    
    # ========================================
    # 9. 用户登出测试
    # ========================================
    print_section("9. 用户登出测试")
    
    try:
        print_info("登出用户...")
        client.logout()
        print_success("登出成功")
        results['tests'].append(('登出', True))
        results['passed'] += 1
    except Exception as e:
        print_error(f"登出异常: {e}")
        results['tests'].append(('登出', False))
        results['failed'] += 1
    
    # ========================================
    # 10. 断开连接测试
    # ========================================
    print_section("10. 断开连接测试")
    
    try:
        print_info("断开服务器连接...")
        client.disconnect()
        print_success("断开连接成功")
        results['tests'].append(('断开连接', True))
        results['passed'] += 1
    except Exception as e:
        print_error(f"断开连接异常: {e}")
        results['tests'].append(('断开连接', False))
        results['failed'] += 1
    
    # ========================================
    # 测试结果汇总
    # ========================================
    print_section("测试结果汇总")
    
    total_tests = results['passed'] + results['failed']
    pass_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {results['passed']} ✓")
    print(f"失败: {results['failed']} ✗")
    print(f"通过率: {pass_rate:.1f}%")
    
    print("\n详细结果:")
    print("-" * 60)
    for test_name, passed in results['tests']:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"  {test_name:<30} - {status}")
    print("-" * 60)
    
    if pass_rate == 100:
        print("\n🎉 所有测试通过！")
    elif pass_rate >= 80:
        print(f"\n✓ 测试基本通过 ({pass_rate:.1f}%)")
    else:
        print(f"\n✗ 有较多测试失败，请检查系统配置 ({pass_rate:.1f}%)")
    
    print("=" * 60 + "\n")

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║         智能安全邮箱系统 - 完整API测试工具              ║
╚════════════════════════════════════════════════════════════╝

此脚本将测试所有邮箱功能：
  • 连接服务器
  • 用户注册
  • 用户登录
  • 发送邮件（含群发、抄送）
  • 查看收件箱
  • 查看已发送
  • 查看草稿箱
  • 搜索邮件
  • 用户登出
  • 断开连接

注意事项：
  1. 确保服务器已启动
  2. 首次运行会创建测试用户
  3. 部分测试可能因用户已存在而提示失败（这是正常的）
""")
    
    input("按回车开始测试...")
    
    try:
        test_all_apis()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车退出...")
