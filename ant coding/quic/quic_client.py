#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUIC客户端实现
"""

import json
import logging
import asyncio
from typing import List, Optional, Dict
from pathlib import Path

try:
    from aioquic.asyncio import connect
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import StreamDataReceived, QuicEvent
except ImportError:
    print("[-] 错误: 需要安装aioquic")
    print("[-] 请运行: pip install -r requirements_quic.txt")
    exit(1)


class QuicMailClient:
    """QUIC邮件客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8443):
        """
        初始化QUIC客户端
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
        """
        self.host = host
        self.port = port
        self.quic_config = QuicConfiguration(is_client=True)
        self.quic_config.verify_mode = False  # 开发环境不验证证书
        
        self.connection = None
        self.token: Optional[str] = None
        self.current_user: Optional[Dict] = None
        
        self.logger = logging.getLogger("QuicMailClient")
    
    async def connect(self):
        """连接到服务器"""
        try:
            self.connection = await connect(
                self.host,
                self.port,
                configuration=self.quic_config
            )
            
            # 测试连接
            response = await self._send_request({'action': 'ping'})
            if response.get('success'):
                self.logger.info(f"成功连接到服务器 {self.host}:{self.port}")
                return True
            else:
                self.logger.error(f"连接失败")
                return False
                
        except Exception as e:
            self.logger.error(f"连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.connection:
            try:
                if self.token:
                    await self.logout()
                await self.connection.close()
            except:
                pass
            finally:
                self.connection = None
                self.token = None
                self.current_user = None
                self.logger.info("已断开连接")
    
    async def _send_request(self, request: Dict) -> Dict:
        """发送请求并接收响应"""
        try:
            # 创建新的流
            stream_id = self.connection.get_next_available_stream_id()
            
            # 发送请求数据
            request_data = json.dumps(request, ensure_ascii=False).encode('utf-8')
            self.connection.send_stream_data(stream_id, request_data, end_stream=True)
            
            # 等待响应
            async def receive_response():
                while True:
                    event = await self.connection.wait_event()
                    if isinstance(event, StreamDataReceived) and event.stream_id == stream_id:
                        response_data = event.data.decode('utf-8')
                        return json.loads(response_data)
            
            response = await asyncio.wait_for(receive_response(), timeout=10.0)
            return response
            
        except Exception as e:
            self.logger.error(f"发送请求失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def register(self, username: str, password: str, email: str) -> bool:
        """注册新用户"""
        try:
            request = {
                'action': 'register',
                'username': username,
                'password': password,
                'email': email
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                self.logger.info(f"用户 {username} 注册成功")
                return True
            else:
                self.logger.error(f"注册失败: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"注册失败: {e}")
            return False
    
    async def login(self, username: str, password: str) -> bool:
        """用户登录"""
        try:
            request = {
                'action': 'login',
                'username': username,
                'password': password,
                'client_ip': '127.0.0.1'
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                self.token = response.get('token')
                self.current_user = response.get('user', {})
                self.logger.info(f"用户 {username} 登录成功")
                return True
            else:
                self.logger.error(f"登录失败: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"登录失败: {e}")
            return False
    
    async def logout(self) -> bool:
        """用户登出"""
        try:
            if not self.token:
                return True
            
            request = {
                'action': 'logout',
                'token': self.token
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                self.token = None
                self.current_user = None
                self.logger.info("登出成功")
                return True
            else:
                self.logger.error(f"登出失败: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"登出失败: {e}")
            return False
    
    async def send_mail(self, to_addresses: List[str], subject: str, body: str,
                       cc: List[str] = None, bcc: List[str] = None) -> Optional[str]:
        """发送邮件"""
        if not self.token:
            self.logger.error("未登录")
            return None
        
        try:
            # 构建邮件对象
            mail = {
                'mail_id': f"mail_{hash(subject + str(to_addresses))}",
                'subject': subject,
                'body': body,
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'status': 'sent',
                'sender': {
                    'username': self.current_user['username'],
                    'domain': self.current_user['domain']
                },
                'recipients': [
                    {'username': addr.split('@')[0], 'domain': addr.split('@')[1]}
                    for addr in to_addresses
                ]
            }
            
            if cc:
                mail['cc_recipients'] = [
                    {'username': addr.split('@')[0], 'domain': addr.split('@')[1]}
                    for addr in cc
                ]
            
            if bcc:
                mail['bcc_recipients'] = [
                    {'username': addr.split('@')[0], 'domain': addr.split('@')[1]}
                    for addr in bcc
                ]
            
            request = {
                'action': 'send_mail',
                'token': self.token,
                'mail': mail
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                mail_id = response.get('mail_id')
                self.logger.info(f"邮件发送成功: {mail_id}")
                return mail_id
            else:
                self.logger.error(f"发送失败: {response.get('error')}")
                return None
                
        except Exception as e:
            self.logger.error(f"发送失败: {e}")
            return None
    
    async def get_mailbox(self, mailbox_type: str = "inbox") -> List[Dict]:
        """获取邮箱内容"""
        if not self.token:
            self.logger.error("未登录")
            return []
        
        try:
            request = {
                'action': 'get_mailbox',
                'token': self.token,
                'mailbox_type': mailbox_type
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                mails = response.get('mails', [])
                self.logger.info(f"获取到 {len(mails)} 封邮件")
                return mails
            else:
                self.logger.error(f"获取失败: {response.get('error')}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取失败: {e}")
            return []
    
    async def withdraw_mail(self, mail_id: str) -> bool:
        """撤回邮件"""
        if not self.token:
            self.logger.error("未登录")
            return False
        
        try:
            request = {
                'action': 'withdraw_mail',
                'token': self.token,
                'mail_id': mail_id
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                self.logger.info(f"邮件 {mail_id} 撤回成功")
                return True
            else:
                self.logger.error(f"撤回失败: {response.get('error')}")
                return False
                
        except Exception as e:
            self.logger.error(f"撤回失败: {e}")
            return False
    
    async def search_mail(self, query: str, search_type: str = "all") -> List[Dict]:
        """搜索邮件"""
        if not self.token:
            self.logger.error("未登录")
            return []
        
        try:
            request = {
                'action': 'search_mail',
                'token': self.token,
                'query': query,
                'search_type': search_type
            }
            
            response = await self._send_request(request)
            
            if response.get('success'):
                results = response.get('results', [])
                self.logger.info(f"搜索到 {len(results)} 封邮件")
                return results
            else:
                self.logger.error(f"搜索失败: {response.get('error')}")
                return []
                
        except Exception as e:
            self.logger.error(f"搜索失败: {e}")
            return []


# 使用示例
async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("QUIC邮件客户端测试")
    print("=" * 60)
    
    # 创建客户端
    client = QuicMailClient(host="localhost", port=8443)
    
    try:
        # 连接服务器
        if not await client.connect():
            print("[-] 连接服务器失败")
            return
        
        print("[+] 连接成功!")
        
        # 注册用户
        print("\n[1] 注册用户...")
        if await client.register("testuser", "password123", "testuser@example1.com"):
            print("[+] 注册成功")
        else:
            print("[-] 注册失败（可能用户已存在）")
        
        # 登录
        print("\n[2] 登录...")
        if await client.login("testuser", "password123"):
            print("[+] 登录成功")
        else:
            print("[-] 登录失败")
            return
        
        # 发送邮件
        print("\n[3] 发送邮件...")
        mail_id = await client.send_mail(
            to_addresses=["user2@example1.com"],
            subject="测试邮件",
            body="这是一封测试邮件"
        )
        if mail_id:
            print(f"[+] 邮件发送成功: {mail_id}")
        else:
            print("[-] 邮件发送失败")
        
        # 获取邮箱
        print("\n[4] 获取收件箱...")
        mails = await client.get_mailbox("inbox")
        print(f"[+] 收件箱中有 {len(mails)} 封邮件")
        for i, mail in enumerate(mails[:3], 1):
            print(f"    {i}. {mail['subject']}")
        
        # 搜索邮件
        print("\n[5] 搜索邮件...")
        results = await client.search_mail("测试")
        print(f"[+] 搜索到 {len(results)} 封邮件")
        
        # 登出
        print("\n[6] 登出...")
        await client.logout()
        print("[+] 已登出")
        
    except KeyboardInterrupt:
        print("\n[!] 用户中断")
    finally:
        await client.disconnect()
        print("\n[+] 客户端已关闭")


if __name__ == "__main__":
    asyncio.run(main())
