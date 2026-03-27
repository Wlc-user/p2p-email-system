#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QUIC服务器实现
"""

import json
import logging
import asyncio
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime

try:
    from aioquic.asyncio import serve
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.connection import QuicConnection
    from aioquic.quic.events import QuicEvent, StreamDataReceived
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    import time
except ImportError:
    print("[-] 错误: 需要安装aioquic")
    print("[-] 请运行: pip install -r requirements_quic.txt")
    exit(1)

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from server.mail_handler import MailHandler
from server.storage_manager import StorageManager
from server.security import SecurityManager


class QuicMailServer:
    """QUIC邮件服务器"""
    
    def __init__(self, config: Dict, domain: str):
        self.domain = domain
        self.config = config
        self.storage_manager = StorageManager(config['data_path'])
        self.security_manager = SecurityManager(config)
        self.mail_handler = MailHandler(self.storage_manager, self.security_manager)
        
        self.active_sessions: Dict[str, Dict] = {}
        self.logger = logging.getLogger(f"QuicServer.{domain}")
    
    def handle_request(self, request: Dict) -> Dict:
        """处理客户端请求"""
        try:
            action = request.get('action')
            
            # 心跳检测
            if action == 'ping':
                return {'success': True, 'message': 'pong'}
            
            # 用户注册
            elif action == 'register':
                result = self.mail_handler.register_user(
                    request['username'],
                    request['password'],
                    request['email']
                )
                return result
            
            # 用户登录
            elif action == 'login':
                result = self.mail_handler.login_user(
                    request['username'],
                    request['password'],
                    request.get('client_ip', '127.0.0.1')
                )
                if result.get('success'):
                    token = str(hash(f"{request['username']}_{time.time()}"))
                    self.active_sessions[token] = result.get('user', {})
                    result['token'] = token
                return result
            
            # 用户登出
            elif action == 'logout':
                token = request.get('token')
                if token in self.active_sessions:
                    del self.active_sessions[token]
                return {'success': True, 'message': '登出成功'}
            
            # 发送邮件
            elif action == 'send_mail':
                token = request.get('token')
                user_info = self.active_sessions.get(token)
                if not user_info:
                    return {'success': False, 'error': '未授权'}
                
                result = self.mail_handler.send_mail(
                    sender=user_info,
                    mail=request['mail']
                )
                return result
            
            # 获取邮箱
            elif action == 'get_mailbox':
                token = request.get('token')
                user_info = self.active_sessions.get(token)
                if not user_info:
                    return {'success': False, 'error': '未授权'}
                
                result = self.mail_handler.get_mailbox(
                    username=user_info['username'],
                    mailbox_type=request.get('mailbox_type', 'inbox')
                )
                return result
            
            # 撤回邮件
            elif action == 'withdraw_mail':
                token = request.get('token')
                user_info = self.active_sessions.get(token)
                if not user_info:
                    return {'success': False, 'error': '未授权'}
                
                result = self.mail_handler.withdraw_mail(
                    username=user_info['username'],
                    mail_id=request['mail_id']
                )
                return result
            
            # 搜索邮件
            elif action == 'search_mail':
                token = request.get('token')
                user_info = self.active_sessions.get(token)
                if not user_info:
                    return {'success': False, 'error': '未授权'}
                
                result = self.mail_handler.search_mail(
                    username=user_info['username'],
                    query=request['query'],
                    search_type=request.get('search_type', 'all')
                )
                return result
            
            else:
                return {'success': False, 'error': '未知操作'}
                
        except Exception as e:
            self.logger.error(f"处理请求失败: {e}")
            return {'success': False, 'error': str(e)}


class QuicServerProtocol(QuicConnectionProtocol):
    """QUIC服务器协议"""
    
    def __init__(self, *args, mail_server: QuicMailServer, **kwargs):
        super().__init__(*args, **kwargs)
        self.mail_server = mail_server
    
    def quic_event_received(self, event: QuicEvent):
        """处理QUIC事件"""
        if isinstance(event, StreamDataReceived):
            try:
                # 解析请求数据
                request_data = event.data.decode('utf-8')
                request = json.loads(request_data)
                
                # 处理请求
                response = self.mail_server.handle_request(request)
                
                # 发送响应
                response_data = json.dumps(response, ensure_ascii=False).encode('utf-8')
                self._quic.send_stream_data(event.stream_id, response_data, end_stream=True)
                
            except Exception as e:
                self.mail_server.logger.error(f"处理事件失败: {e}")
                error_response = {'success': False, 'error': str(e)}
                response_data = json.dumps(error_response, ensure_ascii=False).encode('utf-8')
                self._quic.send_stream_data(event.stream_id, response_data, end_stream=True)


def generate_self_signed_cert():
    """生成自签名证书"""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    
    # 生成私钥
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # 生成证书
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SmartMail"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256(), default_backend())
    
    return cert, private_key


async def start_quic_server(config: Dict, domain: str, host: str = "::", port: int = 8443):
    """启动QUIC服务器"""
    # 创建QUIC配置
    quic_config = QuicConfiguration(is_client=False)
    
    # 生成或加载证书
    cert_dir = Path("certificates")
    cert_dir.mkdir(exist_ok=True)
    
    cert_file = cert_dir / f"{domain}.crt"
    key_file = cert_dir / f"{domain}.key"
    
    if not cert_file.exists() or not key_file.exists():
        from datetime import timedelta
        logging.info(f"生成自签名证书: {domain}")
        cert, private_key = generate_self_signed_cert()
        
        # 保存证书
        with open(cert_file, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_file, 'wb') as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
    
    # 加载证书和私钥
    quic_config.load_cert_chain(cert_file, key_file)
    
    # 创建邮件服务器
    mail_server = QuicMailServer(config, domain)
    
    # 启动QUIC服务器
    logging.info(f"启动QUIC服务器: {domain} - 端口 {port}")
    
    await serve(
        host,
        port,
        configuration=quic_config,
        create_protocol=lambda: QuicServerProtocol(
            quic_configuration=quic_config,
            mail_server=mail_server
        )
    )


if __name__ == "__main__":
    import sys
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 加载配置
    if len(sys.argv) > 2:
        config_path = sys.argv[1]
        domain = sys.argv[2]
        port = int(sys.argv[3]) if len(sys.argv) > 3 else 8443
    else:
        config_path = "config/domain1_config.json"
        domain = "example1.com"
        port = 8443
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 启动服务器
    try:
        asyncio.run(start_quic_server(config, domain, "0.0.0.0", port))
    except KeyboardInterrupt:
        logging.info("服务器停止")
