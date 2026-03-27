#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户端UI界面 - 提供命令行用户界面
"""

import os
import sys
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import WordCompleter
    from prompt_toolkit.formatted_text import HTML
    from prompt_toolkit.styles import Style
    from prompt_toolkit.key_binding import KeyBindings
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    print("提示: 安装 prompt-toolkit 以获得更好的用户体验: pip install prompt-toolkit")


class ClientUI:
    """客户端用户界面"""
    
    def __init__(self, mail_client):
        """
        初始化UI
        
        Args:
            mail_client: MailClient实例
        """
        self.client = mail_client
        self.current_menu = "main"
        self.running = True
        
        # 命令补全器
        self.commands = {
            "main": ["connect", "register", "login", "exit", "help", "about"],
            "connected": ["disconnect", "register", "login", "exit", "help"],
            "logged_in": ["compose", "inbox", "sent", "drafts", "search", 
                         "withdraw", "logout", "exit", "help", "profile", "groups"],
            "compose": ["send", "save", "attach", "cancel", "help"],
            "inbox": ["read", "reply", "delete", "back", "help", "refresh"]
        }
        
        # 样式
        self.style = Style.from_dict({
            'title': '#ff6b6b bold',
            'success': '#51cf66',
            'error': '#ff6b6b',
            'warning': '#fcc419',
            'info': '#339af0',
            'prompt': '#868e96',
            'menu': '#cc5de8',
            'command': '#20c997'
        })
        
        # 键盘绑定
        self.bindings = KeyBindings()
        
        # 初始化提示会话
        if PROMPT_TOOLKIT_AVAILABLE:
            self.session = PromptSession(
                style=self.style,
                key_bindings=self.bindings
            )
    
    def _get_prompt(self) -> str:
        """获取当前提示符"""
        if self.client.current_user:
            username = self.client.current_user.get('username', 'unknown')
            domain = self.client.current_domain or 'unknown'
            return HTML(f'<prompt>[{username}@{domain}]</prompt> <command>&gt;</command> ')
        elif self.client.connected:
            domain = self.client.current_domain or 'unknown'
            return HTML(f'<prompt>[{domain}]</prompt> <command>&gt;</command> ')
        else:
            return HTML('<prompt>[未连接]</prompt> <command>&gt;</command> ')
    
    def _get_completer(self) -> Optional[WordCompleter]:
        """获取命令补全器"""
        if not PROMPT_TOOLKIT_AVAILABLE:
            return None
        
        current_commands = self.commands.get(self.current_menu, [])
        return WordCompleter(current_commands, ignore_case=True)
    
    def _print_header(self):
        """打印头部信息"""
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "=" * 60)
        print("智能安全邮箱系统 - 客户端".center(60))
        print("=" * 60)
        
        if self.client.current_user:
            user = self.client.current_user
            print(f"用户: {user.get('username')}@{self.client.current_domain}")
            print(f"邮箱: {user.get('email')}")
            print(f"登录时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        elif self.client.connected:
            print(f"服务器: {self.client.current_domain}")
            print("状态: 已连接，未登录")
        else:
            print("状态: 未连接")
        
        print("=" * 60 + "\n")
    
    def _print_menu(self, menu_name: str):
        """打印菜单选项"""
        commands = self.commands.get(menu_name, [])
        
        print(f"\n可用命令 ({menu_name}):")
        print("-" * 40)
        
        for i, cmd in enumerate(commands, 1):
            desc = self._get_command_desc(cmd)
            print(f"{i:2}. {cmd:<15} - {desc}")
        
        print("-" * 40)
    
    def _get_command_desc(self, command: str) -> str:
        """获取命令描述"""
        descriptions = {
            # 主要命令
            "connect": "连接到服务器",
            "disconnect": "断开服务器连接",
            "register": "注册新用户",
            "login": "用户登录",
            "logout": "用户登出",
            "exit": "退出程序",
            "help": "显示帮助信息",
            "about": "关于程序",
            
            # 邮件管理
            "compose": "编写新邮件",
            "inbox": "查看收件箱",
            "sent": "查看已发送邮件",
            "drafts": "查看草稿箱",
            "search": "搜索邮件",
            "withdraw": "撤回邮件",
            "profile": "查看用户资料",
            "groups": "管理群组",
            
            # 编写邮件
            "send": "发送邮件",
            "save": "保存草稿",
            "attach": "添加附件",
            "cancel": "取消编写",
            
            # 收件箱
            "read": "阅读邮件",
            "reply": "回复邮件",
            "delete": "删除邮件",
            "back": "返回上级菜单",
            "refresh": "刷新邮件列表"
        }
        
        return descriptions.get(command, "暂无描述")
    
    def _get_input(self, prompt: str = None) -> str:
        """获取用户输入"""
        if prompt is None:
            prompt = self._get_prompt()
        
        if PROMPT_TOOLKIT_AVAILABLE:
            try:
                return self.session.prompt(
                    prompt,
                    completer=self._get_completer()
                ).strip()
            except KeyboardInterrupt:
                return ""
            except EOFError:
                self.running = False
                return "exit"
        else:
            try:
                if isinstance(prompt, str):
                    print(prompt, end='')
                return input().strip()
            except KeyboardInterrupt:
                return ""
            except EOFError:
                self.running = False
                return "exit"
    
    def _print_success(self, message: str):
        """打印成功消息"""
        if PROMPT_TOOLKIT_AVAILABLE:
            print(HTML(f'<success>✓</success> {message}'))
        else:
            print(f"[成功] {message}")
    
    def _print_error(self, message: str):
        """打印错误消息"""
        if PROMPT_TOOLKIT_AVAILABLE:
            print(HTML(f'<error>✗</error> {message}'))
        else:
            print(f"[错误] {message}")
    
    def _print_warning(self, message: str):
        """打印警告消息"""
        if PROMPT_TOOLKIT_AVAILABLE:
            print(HTML(f'<warning>!</warning> {message}'))
        else:
            print(f"[警告] {message}")
    
    def _print_info(self, message: str):
        """打印信息消息"""
        if PROMPT_TOOLKIT_AVAILABLE:
            print(HTML(f'<info>i</info> {message}'))
        else:
            print(f"[信息] {message}")
    
    def run(self):
        """运行UI主循环"""
        self._print_header()
        self._print_menu("main")
        
        while self.running:
            try:
                command = self._get_input()
                
                if not command:
                    continue
                
                # 处理命令
                self._handle_command(command.lower())
                
            except Exception as e:
                self._print_error(f"程序错误: {str(e)}")
    
    def _handle_command(self, command: str):
        """处理用户命令"""
        # 退出命令
        if command in ["exit", "quit", "q"]:
            self._handle_exit()
            return
        
        # 帮助命令
        if command in ["help", "?"]:
            self._print_header()
            self._print_menu(self.current_menu)
            return
        
        # 关于命令
        if command == "about":
            self._handle_about()
            return
        
        # 处理数字输入（对应菜单编号）
        if command.isdigit():
            cmd_index = int(command) - 1
            current_commands = self.commands.get(self.current_menu, [])
            if 0 <= cmd_index < len(current_commands):
                command = current_commands[cmd_index]
            else:
                self._print_error(f"无效的命令编号: {command}")
                return
        
        # 根据当前状态处理命令
        if self.client.current_user:
            self._handle_logged_in_commands(command)
        elif self.client.connected:
            self._handle_connected_commands(command)
        else:
            self._handle_disconnected_commands(command)
    
    def _handle_disconnected_commands(self, command: str):
        """处理未连接状态命令"""
        if command == "connect":
            self._handle_connect()
        elif command == "register":
            self._handle_register()
        elif command == "login":
            self._handle_login()
        else:
            self._print_error(f"未知命令: {command}")
            self._print_info("使用 'help' 查看可用命令")
    
    def _handle_connected_commands(self, command: str):
        """处理已连接未登录状态命令"""
        if command == "disconnect":
            self.client.disconnect()
            self.current_menu = "main"
            self._print_header()
            self._print_menu("main")
            self._print_success("已断开连接")
        elif command == "register":
            self._handle_register()
            self._print_header()
            self._print_menu("connected")
        elif command == "login":
            self._handle_login()
        else:
            self._print_error(f"未知命令: {command}")
            self._print_info("使用 'help' 查看可用命令")
    
    def _handle_logged_in_commands(self, command: str):
        """处理已登录状态命令"""
        if command == "compose":
            self._handle_compose()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "inbox":
            self._handle_inbox()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "sent":
            self._handle_sent()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "drafts":
            self._handle_drafts()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "search":
            self._handle_search()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "withdraw":
            self._handle_withdraw()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "logout":
            self._handle_logout()
        elif command == "profile":
            self._handle_profile()
            self._print_header()
            self._print_menu("logged_in")
        elif command == "groups":
            self._handle_groups()
            self._print_header()
            self._print_menu("logged_in")
        else:
            self._print_error(f"未知命令: {command}")
            self._print_info("使用 'help' 查看可用命令")
        
        # 登录后刷新菜单
        if self.client.current_user:
            self._print_header()
            self._print_menu("logged_in")
    
    def _handle_exit(self):
        """处理退出命令"""
        self._print_info("正在退出...")
        self.client.disconnect()
        self.running = False
        print("再见！")
    
    def _handle_about(self):
        """显示关于信息"""
        print("\n" + "=" * 60)
        print("关于智能安全邮箱系统".center(60))
        print("=" * 60)
        print("版本: 1.0.0")
        print("作者: 智能安全邮箱开发团队")
        print("功能:")
        print("  • 双域名邮箱服务器")
        print("  • 用户注册/登录系统")
        print("  • 邮件收发管理")
        print("  • 邮件撤回功能")
        print("  • 智能搜索和分类")
        print("  • 群组邮件功能")
        print("  • 全面的安全防护")
        print("=" * 60 + "\n")
    
    def _handle_connect(self):
        """处理连接命令"""
        print("\n选择要连接的服务器域名:")
        print("1. example1.com (端口: 8080)")
        print("2. example2.com (端口: 8081)")
        print("3. 自定义服务器")
        
        choice = input("请选择 (1-3): ").strip()
        
        if choice == "1":
            domain = "example1.com"
        elif choice == "2":
            domain = "example2.com"
        elif choice == "3":
            domain = input("请输入域名: ").strip()
            host = input("请输入服务器地址 (默认: 127.0.0.1): ").strip() or "127.0.0.1"
            port = input("请输入端口号: ").strip()
            
            try:
                port = int(port)
                # 保存到配置
                if domain not in self.client.config['servers']:
                    self.client.config['servers'][domain] = {"host": host, "port": port}
                    self.client._save_config()
            except ValueError:
                self._print_error("端口号必须是数字")
                return
        else:
            self._print_error("无效选择")
            return
        
        self._print_info(f"正在连接到 {domain}...")
        
        if self.client.connect_to_server(domain):
            self.current_menu = "connected"
            self._print_header()
            self._print_menu("connected")
            self._print_success(f"已连接到 {domain}")
        else:
            self._print_error(f"连接到 {domain} 失败")
    
    def _handle_register(self):
        """处理注册命令"""
        if not self.client.connected:
            self._print_error("请先连接到服务器")
            return
        
        print("\n用户注册")
        print("-" * 40)
        
        username = input("用户名: ").strip()
        password = input("密码: ").strip()
        confirm_password = input("确认密码: ").strip()
        email = input("邮箱地址: ").strip()
        
        if not username or not password or not email:
            self._print_error("所有字段都是必填的")
            return
        
        if password != confirm_password:
            self._print_error("两次输入的密码不一致")
            return
        
        if self.client.register_user(username, password, email):
            self._print_success("注册成功！请使用 login 命令登录")
        else:
            self._print_error("注册失败")
    
    def _handle_login(self):
        """处理登录命令"""
        if not self.client.connected:
            self._print_error("请先连接到服务器")
            return
        
        print("\n用户登录")
        print("-" * 40)
        
        # 显示最近用户
        recent_users = self.client.config.get('recent_users', [])
        if recent_users:
            print("最近用户:")
            for i, user in enumerate(recent_users[:5], 1):
                print(f"{i}. {user['username']}@{user['domain']}")
            print("0. 输入其他用户名")
            print("-" * 40)
            
            choice = input("请选择用户 (0-5): ").strip()
            
            if choice.isdigit() and 1 <= int(choice) <= len(recent_users[:5]):
                user = recent_users[int(choice) - 1]
                username = user['username']
                domain = user['domain']
                
                # 如果选择了不同域名的用户，需要重新连接
                if domain != self.client.current_domain:
                    self._print_info(f"切换到域名: {domain}")
                    self.client.disconnect()
                    if not self.client.connect_to_server(domain):
                        self._print_error(f"切换到 {domain} 失败")
                        return
            else:
                username = input("用户名: ").strip()
        else:
            username = input("用户名: ").strip()
        
        password = input("密码: ").strip()
        remember_me = input("记住我? (y/n, 默认: n): ").strip().lower() == 'y'
        
        if not username or not password:
            self._print_error("用户名和密码是必填的")
            return
        
        self._print_info("正在登录...")
        
        if self.client.login(username, password, remember_me):
            self.current_menu = "logged_in"
            self._print_header()
            self._print_menu("logged_in")
            self._print_success("登录成功！")
        else:
            self._print_error("登录失败")
    
    def _handle_logout(self):
        """处理登出命令"""
        self.client.logout()
        self.current_menu = "connected"
        self._print_header()
        self._print_menu("connected")
        self._print_success("已登出")
    
    def _handle_compose(self):
        """处理编写邮件命令"""
        print("\n编写新邮件")
        print("-" * 40)
        print("输入 'send' 发送邮件，'save' 保存草稿，'cancel' 取消")
        print("-" * 40)
        
        to_addresses_input = input("收件人 (多个用逗号分隔): ").strip()
        cc_addresses_input = input("抄送 (多个用逗号分隔，直接回车跳过): ").strip()
        bcc_addresses_input = input("密送 (多个用逗号分隔，直接回车跳过): ").strip()
        subject = input("主题: ").strip()
        
        print("\n正文 (输入 '.' 单独一行结束):")
        print("-" * 40)
        
        body_lines = []
        while True:
            line = input()
            if line == ".":
                break
            body_lines.append(line)
        
        body = "\n".join(body_lines)
        
        # 解析地址
        to_addresses = [addr.strip() for addr in to_addresses_input.split(",") if addr.strip()]
        cc_addresses = [addr.strip() for addr in cc_addresses_input.split(",") if addr.strip()] if cc_addresses_input else []
        bcc_addresses = [addr.strip() for addr in bcc_addresses_input.split(",") if addr.strip()] if bcc_addresses_input else []
        
        while True:
            action = input("\n操作 (send/save/cancel): ").strip().lower()
            
            if action == "send":
                if not to_addresses:
                    self._print_error("必须指定至少一个收件人")
                    continue
                
                if not subject:
                    self._print_warning("邮件主题为空，是否继续? (y/n): ")
                    if input().strip().lower() != 'y':
                        continue
                
                mail_id = self.client.send_mail(
                    to_addresses=to_addresses,
                    subject=subject,
                    body=body,
                    cc_addresses=cc_addresses,
                    bcc_addresses=bcc_addresses
                )
                
                if mail_id:
                    self._print_success(f"邮件发送成功！邮件ID: {mail_id}")
                else:
                    self._print_error("邮件发送失败")
                break
                
            elif action == "save":
                # TODO: 实现保存草稿功能
                self._print_info("草稿保存功能正在开发中...")
                break
                
            elif action == "cancel":
                self._print_info("邮件编写已取消")
                break
                
            else:
                self._print_error("无效操作")
    
    def _handle_inbox(self):
        """处理收件箱命令"""
        print("\n收件箱")
        print("-" * 60)
        
        mails = self.client.get_mailbox("inbox")
        
        if not mails:
            self._print_info("收件箱为空")
            return
        
        # 显示邮件列表
        for i, mail in enumerate(mails, 1):
            sender = f"{mail['sender']['username']}@{mail['sender']['domain']}"
            timestamp = mail['timestamp'][:19].replace("T", " ")
            subject = mail['subject'][:40] + "..." if len(mail['subject']) > 40 else mail['subject']
            
            read_flag = " " if mail.get('is_read', False) else "✉"
            
            print(f"{i:2}. {read_flag} {sender:<25} {subject:<45} {timestamp}")
        
        print("-" * 60)
        print("输入邮件编号查看详情，或输入 'back' 返回")
        
        while True:
            choice = input("\n选择邮件编号: ").strip()
            
            if choice.lower() == "back":
                break
            
            if not choice.isdigit():
                self._print_error("请输入数字编号")
                continue
            
            idx = int(choice) - 1
            if idx < 0 or idx >= len(mails):
                self._print_error("无效的邮件编号")
                continue
            
            self._show_mail_detail(mails[idx])
    
    def _show_mail_detail(self, mail: Dict[str, Any]):
        """显示邮件详情"""
        print("\n" + "=" * 60)
        print("邮件详情".center(60))
        print("=" * 60)
        
        sender = f"{mail['sender']['username']}@{mail['sender']['domain']}"
        recipients = ", ".join([f"{r['username']}@{r['domain']}" for r in mail['recipients']])
        
        print(f"发件人: {sender}")
        print(f"收件人: {recipients}")
        
        if mail.get('cc_recipients'):
            cc = ", ".join([f"{r['username']}@{r['domain']}" for r in mail['cc_recipients']])
            print(f"抄送: {cc}")
        
        timestamp = mail['timestamp'][:19].replace("T", " ")
        print(f"时间: {timestamp}")
        print(f"主题: {mail['subject']}")
        
        print("\n" + "-" * 60)
        print("正文:")
        print("-" * 60)
        print(mail['body'])
        print("-" * 60)
        
        # 邮件操作
        print("\n操作: reply(回复), delete(删除), back(返回)")
        action = input("选择操作: ").strip().lower()
        
        if action == "reply":
            self._handle_reply(mail)
        elif action == "delete":
            # TODO: 实现删除邮件功能
            self._print_info("删除功能正在开发中...")
        elif action == "back":
            return
        else:
            self._print_error("无效操作")
    
    def _handle_reply(self, original_mail: Dict[str, Any]):
        """处理回复邮件"""
        print("\n快速回复")
        print("-" * 40)
        
        reply_text = input("回复内容: ").strip()
        
        if not reply_text:
            self._print_error("回复内容不能为空")
            return
        
        # 生成快速回复
        mail_id = original_mail.get('mail_id')
        if not mail_id:
            self._print_error("无法获取原邮件ID")
            return
        
        reply_mail_id = self.client.quick_reply(mail_id, reply_text)
        
        if reply_mail_id:
            self._print_success(f"回复发送成功！邮件ID: {reply_mail_id}")
        else:
            self._print_error("回复发送失败")
    
    def _handle_sent(self):
        """处理已发送邮件命令"""
        mails = self.client.get_mailbox("sent")
        
        if not mails:
            self._print_info("已发送邮件为空")
            return
        
        print(f"\n已发送邮件 ({len(mails)} 封)")
        print("-" * 60)
        
        for i, mail in enumerate(mails, 1):
            recipients = ", ".join([f"{r['username']}@{r['domain']}" for r in mail['recipients'][:2]])
            if len(mail['recipients']) > 2:
                recipients += f" 等{len(mail['recipients'])}人"
            
            timestamp = mail['timestamp'][:19].replace("T", " ")
            subject = mail['subject'][:40] + "..." if len(mail['subject']) > 40 else mail['subject']
            
            print(f"{i:2}. 至: {recipients:<30} {subject:<30} {timestamp}")
    
    def _handle_drafts(self):
        """处理草稿箱命令"""
        mails = self.client.get_mailbox("drafts")
        
        if not mails:
            self._print_info("草稿箱为空")
            return
        
        print(f"\n草稿箱 ({len(mails)} 封)")
        print("-" * 60)
        
        for i, mail in enumerate(mails, 1):
            recipients = ", ".join([f"{r['username']}@{r['domain']}" for r in mail['recipients'][:2]])
            timestamp = mail['timestamp'][:19].replace("T", " ")
            subject = mail['subject'][:40] + "..." if len(mail['subject']) > 40 else mail['subject']
            
            print(f"{i:2}. 至: {recipients:<30} {subject:<30} {timestamp}")
    
    def _handle_search(self):
        """处理搜索命令"""
        print("\n邮件搜索")
        print("-" * 40)
        
        query = input("搜索关键词: ").strip()
        
        if not query:
            self._print_error("搜索关键词不能为空")
            return
        
        self._print_info("正在搜索...")
        
        results = self.client.search_mails(query)
        
        if not results:
            self._print_info(f"没有找到包含 '{query}' 的邮件")
            return
        
        print(f"\n搜索结果 ({len(results)} 封)")
        print("-" * 60)
        
        for i, mail in enumerate(results, 1):
            sender = f"{mail['sender']['username']}@{mail['sender']['domain']}"
            timestamp = mail['timestamp'][:19].replace("T", " ")
            subject = mail['subject'][:40] + "..." if len(mail['subject']) > 40 else mail['subject']
            
            print(f"{i:2}. {sender:<25} {subject:<45} {timestamp}")
    
    def _handle_withdraw(self):
        """处理撤回邮件命令"""
        print("\n撤回邮件")
        print("-" * 40)
        
        # 先获取已发送邮件
        sent_mails = self.client.get_mailbox("sent")
        
        if not sent_mails:
            self._print_info("没有可撤回的邮件")
            return
        
        print("最近发送的邮件:")
        for i, mail in enumerate(sent_mails[:10], 1):
            recipients = ", ".join([f"{r['username']}@{r['domain']}" for r in mail['recipients'][:2]])
            timestamp = mail['timestamp'][11:19]  # 只显示时间
            subject = mail['subject'][:30] + "..." if len(mail['subject']) > 30 else mail['subject']
            
            print(f"{i:2}. {recipients:<25} {subject:<35} {timestamp}")
        
        print("-" * 40)
        mail_id = input("输入要撤回的邮件ID (或编号): ").strip()
        
        # 如果是编号，转换为邮件ID
        if mail_id.isdigit():
            idx = int(mail_id) - 1
            if 0 <= idx < len(sent_mails[:10]):
                mail_id = sent_mails[idx].get('mail_id')
            else:
                self._print_error("无效的编号")
                return
        
        if not mail_id:
            self._print_error("必须指定邮件ID")
            return
        
        confirm = input(f"确认要撤回邮件 {mail_id}? (y/n): ").strip().lower()
        
        if confirm == 'y':
            if self.client.withdraw_mail(mail_id):
                self._print_success("邮件撤回成功")
            else:
                self._print_error("邮件撤回失败")
        else:
            self._print_info("撤回已取消")
    
    def _handle_profile(self):
        """处理查看资料命令"""
        if not self.client.current_user:
            self._print_error("用户未登录")
            return
        
        user = self.client.current_user
        
        print("\n用户资料")
        print("-" * 40)
        print(f"用户名: {user.get('username')}")
        print(f"域名: {self.client.current_domain}")
        print(f"邮箱: {user.get('email')}")
        print(f"创建时间: {user.get('created_at')}")
        print(f"最后登录: {user.get('last_login', '从未登录')}")
        print(f"管理员: {'是' if user.get('is_admin') else '否'}")
        print(f"存储使用: {user.get('storage_used_mb', 0):.2f} MB")
        print(f"邮件数量: {user.get('mail_count', 0)}")
        print("-" * 40)
    
    def _handle_groups(self):
        """处理群组管理命令"""
        print("\n群组管理")
        print("-" * 40)
        print("1. 创建群组")
        print("2. 查看我的群组")
        print("3. 发送群组邮件")
        print("4. 返回")
        print("-" * 40)
        
        choice = input("请选择 (1-4): ").strip()
        
        if choice == "1":
            self._handle_create_group()
        elif choice == "2":
            # TODO: 实现查看群组功能
            self._print_info("查看群组功能正在开发中...")
        elif choice == "3":
            self._handle_group_send()
        elif choice == "4":
            return
        else:
            self._print_error("无效选择")


if __name__ == "__main__":
    # 测试UI
    class MockClient:
        def __init__(self):
            self.connected = False
            self.current_user = None
            self.current_domain = None
            self.config = {"servers": {}, "recent_users": []}
        
        def connect_to_server(self, domain):
            self.connected = True
            self.current_domain = domain
            return True
        
        def disconnect(self):
            self.connected = False
            self.current_domain = None
        
        def register_user(self, *args):
            print(f"Mock: Register user {args[0]}")
            return True
        
        def login(self, *args):
            print(f"Mock: Login user {args[0]}")
            self.current_user = {"username": args[0], "email": f"{args[0]}@test.com"}
            return True
        
        def logout(self):
            self.current_user = None
    
    mock_client = MockClient()
    ui = ClientUI(mock_client)
    ui.run()