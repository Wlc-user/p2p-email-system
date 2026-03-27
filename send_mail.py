#!/usr/bin/env python3
"""
交互式P2P邮件发送工具
"""

import asyncio
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ant coding/p2p"))

from p2p_global import P2PEmailNode


async def interactive_mail():
    """交互式邮件系统"""
    print("=" * 60)
    print("  P2P 邮件系统 - 交互式模式")
    print("=" * 60)
    print()

    # 用户选择角色
    print("请选择角色:")
    print("1. Alice (发送方)")
    print("2. Bob (接收方)")
    print()

    choice = input("选择 (1/2): ").strip()

    # 创建节点
    if choice == "1":
        node = P2PEmailNode(seed="alice@example.com", port=8100)
        role = "Alice"
        peer_seed = "bob@example.com"
    else:
        node = P2PEmailNode(seed="bob@example.com", port=8101)
        role = "Bob"
        peer_seed = "alice@example.com"

    # 启动节点
    print(f"\n启动 {role} 的节点...")
    await node.start()

    # 等待对方节点
    print(f"\n等待对方节点启动...")
    print(f"对方需要使用种子: {peer_seed}")
    print("对方节点将自动连接\n")

    # 交换密钥
    from p2p_global import Identity
    _, peer_pub = Identity.id_from_seed(peer_seed)
    peer_id = Identity.pubkey_to_id(peer_pub)

    try:
        node.encryption.derive_shared_secret(peer_pub, peer_id)
        print(f"[OK] 已与 {peer_id[:16]}... 交换密钥")

        # 添加到DHT
        from p2p_global import DHTNode
        node.dht.add_node(DHTNode(peer_id, "127.0.0.1", 8101 if role == "Alice" else 8100))
        print(f"[OK] 已添加到DHT网络\n")

        # 交互式菜单
        while True:
            print("\n" + "=" * 60)
            print(f"{role} 的邮件菜单:")
            print("=" * 60)
            print("1. 发送邮件")
            print("2. 查看收件箱")
            print("3. 查看已发送")
            print("4. 退出")
            print()

            action = input("选择操作: ").strip()

            if action == "1":
                # 发送邮件
                subject = input("邮件主题: ").strip()
                print("邮件内容 (输入空行结束):")
                lines = []
                while True:
                    line = input()
                    if line == "":
                        break
                    lines.append(line)
                body = "\n".join(lines)

                try:
                    msg_id = await node.send_email(peer_id, subject, body)
                    print(f"\n[OK] 邮件已发送! ID: {msg_id[:16]}...")
                except Exception as e:
                    print(f"\n[错误] 发送失败: {e}")

            elif action == "2":
                # 查看收件箱
                node.display_inbox()

            elif action == "3":
                # 查看已发送
                node.display_sent()

            elif action == "4":
                print("\n退出程序...")
                break

            else:
                print("\n无效选择!")

    except Exception as e:
        print(f"\n[错误] {e}")
        print("提示: 请确保对方节点已启动")

    # 停止节点
    await node.stop()
    print("\n[OK] 节点已停止")


async def demo_mode():
    """演示模式 - 自动发送测试邮件"""
    print("=" * 60)
    print("  P2P 邮件系统 - 演示模式")
    print("=" * 60)
    print()

    # 创建两个节点
    alice = P2PEmailNode(seed="alice@example.com", port=8100)
    bob = P2PEmailNode(seed="bob@example.com", port=8101)

    print("启动 Alice 的节点...")
    await alice.start()
    print("启动 Bob 的节点...")
    await bob.start()

    # 交换密钥
    print("\n交换密钥...")
    alice.encryption.derive_shared_secret(bob.pub_key, bob.node_id)
    bob.encryption.derive_shared_secret(alice.pub_key, alice.node_id)
    print("[OK] 密钥交换完成")

    # 添加到DHT
    from p2p_global import DHTNode
    alice.dht.add_node(DHTNode(bob.node_id, "127.0.0.1", 8101))
    bob.dht.add_node(DHTNode(alice.node_id, "127.0.0.1", 8100))
    print("[OK] DHT网络已建立\n")

    # Alice 发送邮件给 Bob
    print("-" * 60)
    print("Alice 发送邮件给 Bob...")
    print("-" * 60)

    await alice.send_email(
        recipient_id=bob.node_id,
        subject="Hello from Alice! (P2P加密邮件)",
        body="这是一封通过P2P网络发送的加密邮件。\n\n"
              "特点:\n"
              "✓ 无需邮件服务器\n"
              "✓ 端到端加密\n"
              "✓ 点对点传输\n"
              "✓ 全球可用"
    )

    await asyncio.sleep(1)

    # Bob 查看收件箱
    print("\n" + "-" * 60)
    print("Bob 的收件箱:")
    print("-" * 60)
    bob.display_inbox()

    # Alice 查看已发送
    print("\n" + "-" * 60)
    print("Alice 的已发送:")
    print("-" * 60)
    alice.display_sent()

    # 保持运行
    print("\n按 Ctrl+C 退出...")
    try:
        await asyncio.sleep(10)
    except KeyboardInterrupt:
        print("\n\n退出中...")

    # 停止
    await alice.stop()
    await bob.stop()

    print("\n" + "=" * 60)
    print("[OK] 演示完成!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n启动模式:")
    print("1. 演示模式 (自动发送测试邮件)")
    print("2. 交互模式 (手动发送邮件)")
    print()

    mode = input("选择模式 (1/2，默认1): ").strip() or "1"

    if mode == "1":
        asyncio.run(demo_mode())
    else:
        asyncio.run(interactive_mail())
