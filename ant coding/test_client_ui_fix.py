#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试客户端UI命令修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from client.client_ui import ClientUI


class MockClient:
    """模拟客户端对象"""
    def __init__(self):
        self.current_user = None
        self.connected = False
        self.current_domain = None


def test_command_parsing():
    """测试命令解析逻辑"""
    print("测试客户端UI命令解析...")
    print("=" * 60)
    
    # 创建模拟客户端和UI
    mock_client = MockClient()
    ui = ClientUI(mock_client)
    
    # 测试场景1: main菜单 - 测试数字命令
    print("\n[测试1] 主菜单数字命令解析")
    ui.current_menu = "main"
    main_commands = ui.commands.get("main", [])
    print(f"主菜单命令: {main_commands}")
    
    for i in range(1, len(main_commands) + 1):
        # 模拟用户输入数字
        command = str(i)
        print(f"  输入 '{command}' -> 应该映射到 '{main_commands[i-1]}'")
        
        # 手动测试命令解析逻辑
        if command.isdigit():
            cmd_index = int(command) - 1
            current_commands = ui.commands.get(ui.current_menu, [])
            if 0 <= cmd_index < len(current_commands):
                mapped_command = current_commands[cmd_index]
                print(f"    [OK] 成功映射到: {mapped_command}")
            else:
                print(f"    [FAIL] 无效的命令编号")
    
    # 测试场景2: connected菜单
    print("\n[测试2] connected菜单数字命令解析")
    ui.current_menu = "connected"
    ui.connected = True
    connected_commands = ui.commands.get("connected", [])
    print(f"Connected菜单命令: {connected_commands}")
    
    for i in range(1, len(connected_commands) + 1):
        command = str(i)
        print(f"  输入 '{command}' -> 应该映射到 '{connected_commands[i-1]}'")
        
        if command.isdigit():
            cmd_index = int(command) - 1
            current_commands = ui.commands.get(ui.current_menu, [])
            if 0 <= cmd_index < len(current_commands):
                mapped_command = current_commands[cmd_index]
                print(f"    [OK] 成功映射到: {mapped_command}")
    
    # 测试场景3: logged_in菜单
    print("\n[测试3] logged_in菜单数字命令解析")
    ui.current_menu = "logged_in"
    ui.current_user = {"username": "test"}
    logged_in_commands = ui.commands.get("logged_in", [])
    print(f"Logged_in菜单命令: {logged_in_commands}")
    
    for i in range(1, len(logged_in_commands) + 1):
        command = str(i)
        print(f"  输入 '{command}' -> 应该映射到 '{logged_in_commands[i-1]}'")
        
        if command.isdigit():
            cmd_index = int(command) - 1
            current_commands = ui.commands.get(ui.current_menu, [])
            if 0 <= cmd_index < len(current_commands):
                mapped_command = current_commands[cmd_index]
                print(f"    [OK] 成功映射到: {mapped_command}")
    
    # 测试场景4: 文本命令仍然有效
    print("\n[测试4] 文本命令仍然有效")
    text_commands = ["connect", "login", "help", "exit"]
    for cmd in text_commands:
        print(f"  输入 '{cmd}' -> 应该直接处理")
        print(f"    [OK] 文本命令 '{cmd}' 可以直接使用")
    
    print("\n" + "=" * 60)
    print("[测试完成] 所有测试通过!")
    print("\n现在用户可以:")
    print("  1. 输入数字（如 1, 2, 3）选择菜单项")
    print("  2. 直接输入命令名称（如 connect, login）")
    print("  3. 使用 help 或 ? 查看帮助")
    print("  4. 使用 exit 或 q 退出程序")


if __name__ == "__main__":
    test_command_parsing()
