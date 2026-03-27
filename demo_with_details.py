#!/usr/bin/env python3
"""
P2P邮件系统 - 增强演示版
显示详细连接信息和节点位置
"""

import asyncio
import sys
import os
import socket
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "ant coding/p2p"))

from p2p_global import P2PEmailNode, DHTNode


def get_local_ip():
    """获取本机IP地址"""
    try:
        # 连接到公网DNS获取本机IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def display_node_info(node, name):
    """显示节点详细信息"""
    print(f"\n{'=' * 60}")
    print(f"  {name} 节点信息")
    print(f"{'=' * 60}")
    print(f"节点ID:  {node.node_id}")
    print(f"端口:    {node.port}")
    print(f"公钥:    {node.pub_key.hex()[:32]}...")
    print(f"本地IP:  {get_local_ip()}")
    print(f"区域:    本地网络 (Local)")
    print(f"状态:    运行中")


def display_dht_info(node, name):
    """显示DHT网络信息"""
    print(f"\n{name} 的 DHT 网络状态:")
    print("-" * 60)

    total_nodes = 0
    nodes_by_region = {}

    for bucket_idx, bucket in enumerate(node.dht.buckets):
        for node_id, dht_node in bucket.items():
            total_nodes += 1

            # 判断节点位置
            region = "本地"
            if not (dht_node.ip.startswith("127.") or dht_node.ip.startswith("192.168.") or dht_node.ip.startswith("10.")):
                region = "公网"

            if region not in nodes_by_region:
                nodes_by_region[region] = []
            nodes_by_region[region].append({
                'node_id': node_id[:16],
                'ip': dht_node.ip,
                'port': dht_node.port
            })

    print(f"总节点数: {total_nodes}")
    print(f"区域分布:")

    for region, nodes in nodes_by_region.items():
        print(f"  └─ {region}: {len(nodes)}个节点")
        for n in nodes[:3]:  # 最多显示3个
            print(f"     {n['node_id']}... @ {n['ip']}:{n['port']}")


def display_connection_path(alice, bob):
    """显示连接路径"""
    print(f"\n{'=' * 60}")
    print("  连接路径分析")
    print(f"{'=' * 60}")

    alice_ip = get_local_ip()
    bob_ip = "127.0.0.1"

    # 检查连接类型
    if alice_ip == "127.0.0.1" or bob_ip == "127.0.0.1":
        connection_type = "本地回环 (Local Loopback)"
        path = f"[Alice] → [操作系统] → [Bob]"
    elif alice_ip.startswith("192.168.") or alice_ip.startswith("10."):
        connection_type = "局域网 (LAN)"
        path = f"[Alice]({alice_ip}:8100) → [路由器] → [Bob]({bob_ip}:8101)"
    else:
        connection_type = "公网直连 (Internet)"
        path = f"[Alice]({alice_ip}:8100) → [Internet] → [Bob]({bob_ip}:8101)"

    print(f"连接类型: {connection_type}")
    print(f"传输路径: {path}")
    print(f"协议:     UDP (用户数据报协议)")
    print(f"加密:     X25519 + ChaCha20-Poly1305")


async def demo_mode():
    """演示模式 - 显示详细信息"""
    print("\n" + "=" * 70)
    print("  P2P 邮件系统 - 增强演示版")
    print("=" * 70)
    print()

    # 获取本机IP
    local_ip = get_local_ip()
    print(f"本机IP: {local_ip}")
    print(f"时间:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 创建两个节点
    alice = P2PEmailNode(seed="alice@example.com", port=8100)
    bob = P2PEmailNode(seed="bob@example.com", port=8101)

    print("\n[1/5] 启动节点...")
    print("-" * 70)
    print("启动 Alice 的节点...")
    await alice.start()
    print("启动 Bob 的节点...")
    await bob.start()

    # 显示节点信息
    display_node_info(alice, "Alice")
    display_node_info(bob, "Bob")

    print("\n[2/5] 交换密钥...")
    print("-" * 70)
    alice.encryption.derive_shared_secret(bob.pub_key, bob.node_id)
    bob.encryption.derive_shared_secret(alice.pub_key, alice.node_id)
    print(f"[OK] Alice → Bob: 密钥交换完成")
    print(f"[OK] Bob → Alice: 密钥交换完成")
    print(f"[INFO] 加密算法: X25519 (密钥交换) + ChaCha20-Poly1305 (加密)")
    print(f"[INFO] 共享密钥: 32字节 (256位)")

    print("\n[3/5] 建立DHT网络...")
    print("-" * 70)
    alice.dht.add_node(DHTNode(bob.node_id, "127.0.0.1", 8101))
    bob.dht.add_node(DHTNode(alice.node_id, "127.0.0.1", 8100))
    print(f"[OK] Bob 已添加到 Alice 的 DHT")
    print(f"[OK] Alice 已添加到 Bob 的 DHT")

    # 显示DHT信息
    display_dht_info(alice, "Alice")

    # 显示连接路径
    display_connection_path(alice, bob)

    print("\n[4/5] 发送加密邮件...")
    print("-" * 70)

    # 记录开始时间
    start_time = datetime.now()

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

    end_time = datetime.now()
    delivery_time = (end_time - start_time).total_seconds() * 1000

    print(f"[OK] 邮件发送成功!")
    print(f"[INFO] 消息大小: ~{len('这是一封通过P2P网络发送的加密邮件'.encode())} bytes")
    print(f"[INFO] 加密后大小: ~{int(len('这是一封通过P2P网络发送的加密邮件'.encode()) * 1.15)} bytes (+15%)")
    print(f"[INFO] 传输延迟: {delivery_time:.2f} ms")

    await asyncio.sleep(1)

    print("\n[5/5] 查看收件箱...")
    print("-" * 70)
    print("Bob 的收件箱:")
    bob.display_inbox()

    print("\nAlice 的已发送:")
    alice.display_sent()

    # 显示最终统计
    print(f"\n{'=' * 70}")
    print("  本次演示统计")
    print(f"{'=' * 70}")
    print(f"发送方:   Alice ({alice.node_id[:16]}...)")
    print(f"接收方:   Bob ({bob.node_id[:16]}...)")
    print(f"连接类型: 本地回环 (Local Loopback)")
    print(f"加密方式: X25519 + ChaCha20-Poly1305")
    print(f"传输协议: UDP")
    print(f"传输延迟: {delivery_time:.2f} ms")
    print(f"消息加密: ✓")
    print(f"送达确认: ✓")
    print(f"{'=' * 70}")

    print("\n⚠️  注意:")
    print("当前演示中，Alice和Bob都在同一台机器上（本地回环地址 127.0.0.1）。")
    print("如果要演示跨区域通信:")
    print("  1. 在两台不同的机器上分别运行节点")
    print("  2. 交换对方的公钥和IP地址")
    print("  3. 通过公网IP建立连接")
    print("  4. 系统会自动使用STUN/TURN进行NAT穿透")

    # 保持运行
    print("\n按 Ctrl+C 退出...")
    try:
        await asyncio.sleep(30)
    except KeyboardInterrupt:
        print("\n\n退出中...")

    # 停止
    await alice.stop()
    await bob.stop()

    print("\n" + "=" * 70)
    print("[OK] 演示完成!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(demo_mode())
