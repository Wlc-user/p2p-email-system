"""
简单的 P2P 邮件中继服务器
用于节点发现和消息转发
"""

import asyncio
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class RelayHandler(BaseHTTPRequestHandler):
    """中继服务器处理器"""

    # 在线节点列表
    active_nodes = {}

    # 离线消息存储
    offline_messages = {}

    def log_message(self, format, *args):
        """重写日志方法，去除多余信息"""
        logger.info(f"{self.client_address[0]} - {format % args}")

    def _json_response(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self._json_response({}, 200)

    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            # 获取节点信息
            if path == '/api/node':
                query = parse_qs(parsed_path.query)
                node_id = query.get('node_id', [''])[0]

                if node_id in self.active_nodes:
                    self._json_response({
                        'success': True,
                        'node': self.active_nodes[node_id]
                    })
                else:
                    self._json_response({
                        'success': False,
                        'error': '节点不在线'
                    })
                return

            # 获取所有在线节点
            elif path == '/api/nodes':
                self._json_response({
                    'success': True,
                    'nodes': list(self.active_nodes.keys()),
                    'count': len(self.active_nodes)
                })
                return

            # 获取离线消息
            elif path == '/api/messages':
                query = parse_qs(parsed_path.query)
                node_id = query.get('node_id', [''])[0]

                if node_id in self.offline_messages:
                    messages = self.offline_messages.pop(node_id, [])
                    self._json_response({
                        'success': True,
                        'messages': messages
                    })
                else:
                    self._json_response({
                        'success': True,
                        'messages': []
                    })
                return

            # 健康检查
            elif path == '/api/health':
                self._json_response({
                    'success': True,
                    'status': 'running',
                    'active_nodes': len(self.active_nodes),
                    'timestamp': time.time()
                })
                return

            # 未知路径
            else:
                self._json_response({'success': False, 'error': '未知路径'}, 404)

        except Exception as e:
            logger.error(f"GET请求处理错误: {e}")
            self._json_response({'success': False, 'error': str(e)}, 500)

    def do_POST(self):
        """处理 POST 请求"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8')) if content_length > 0 else {}

            # 节点上线
            if path == '/api/hello':
                node_id = body.get('node_id')
                ip = body.get('ip', self.client_address[0])
                port = body.get('port')
                public_key = body.get('public_key')

                if not node_id:
                    self._json_response({'success': False, 'error': '缺少node_id'}, 400)
                    return

                # 更新节点信息
                self.active_nodes[node_id] = {
                    'ip': ip,
                    'port': port,
                    'public_key': public_key,
                    'last_seen': time.time()
                }

                logger.info(f"节点上线: {node_id[:16]}... ({ip}:{port})")

                # 检查是否有离线消息
                if node_id in self.offline_messages:
                    messages = self.offline_messages[node_id]
                    logger.info(f"发现 {len(messages)} 条离线消息给 {node_id[:16]}...")

                self._json_response({
                    'success': True,
                    'message': '节点已上线',
                    'has_messages': node_id in self.offline_messages
                })
                return

            # 转发消息
            elif path == '/api/relay':
                sender_id = body.get('sender_id')
                recipient_id = body.get('recipient_id')
                message = body.get('message')

                if not all([sender_id, recipient_id, message]):
                    self._json_response({'success': False, 'error': '缺少必要参数'}, 400)
                    return

                # 检查接收者是否在线
                if recipient_id in self.active_nodes:
                    recipient = self.active_nodes[recipient_id]
                    logger.info(f"转发消息: {sender_id[:16]}... -> {recipient_id[:16]}...")

                    # 返回接收者信息，让发送者直接连接
                    self._json_response({
                        'success': True,
                        'message': '接收者在线',
                        'recipient': {
                            'node_id': recipient_id,
                            'ip': recipient['ip'],
                            'port': recipient['port'],
                            'public_key': recipient['public_key']
                        }
                    })
                else:
                    # 接收者不在线，存储离线消息
                    if recipient_id not in self.offline_messages:
                        self.offline_messages[recipient_id] = []

                    self.offline_messages[recipient_id].append({
                        'sender_id': sender_id,
                        'message': message,
                        'timestamp': time.time()
                    })

                    logger.info(f"存储离线消息: {sender_id[:16]}... -> {recipient_id[:16]}...")

                    self._json_response({
                        'success': True,
                        'message': '接收者不在线，消息已存储'
                    })
                return

            # 清理过期节点
            elif path == '/api/cleanup':
                current_time = time.time()
                timeout = body.get('timeout', 3600)  # 默认1小时超时

                expired = []
                for node_id, info in self.active_nodes.items():
                    if current_time - info['last_seen'] > timeout:
                        expired.append(node_id)

                for node_id in expired:
                    del self.active_nodes[node_id]
                    logger.info(f"节点过期: {node_id[:16]}...")

                self._json_response({
                    'success': True,
                    'cleaned': len(expired),
                    'active': len(self.active_nodes)
                })
                return

            # 未知路径
            else:
                self._json_response({'success': False, 'error': '未知路径'}, 404)

        except Exception as e:
            logger.error(f"POST请求处理错误: {e}")
            self._json_response({'success': False, 'error': str(e)}, 500)


def start_relay_server(host='0.0.0.0', port=9000):
    """启动中继服务器"""

    server = HTTPServer((host, port), RelayHandler)

    logger.info("=" * 60)
    logger.info("P2P邮件中继服务器启动")
    logger.info("=" * 60)
    logger.info(f"服务器地址: http://{host}:{port}")
    logger.info("")
    logger.info("API端点:")
    logger.info(f"  GET  /api/health      - 健康检查")
    logger.info(f"  GET  /api/nodes       - 获取在线节点列表")
    logger.info(f"  GET  /api/node?node_id=xxx - 查询节点信息")
    logger.info(f"  GET  /api/messages?node_id=xxx - 获取离线消息")
    logger.info(f"  POST /api/hello       - 节点上线")
    logger.info(f"  POST /api/relay       - 转发消息")
    logger.info(f"  POST /api/cleanup     - 清理过期节点")
    logger.info("")
    logger.info("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("\n服务器停止")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='P2P邮件中继服务器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=9000, help='监听端口')

    args = parser.parse_args()

    start_relay_server(args.host, args.port)
