"""
企业级CS架构邮件系统
支持双域名、附件、撤回、限流、安全防护、智能功能
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import os
import sqlite3
import datetime
import secrets
import functools
import logging
import time
import re
import json
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Flask 应用
app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 数据库路径(支持多域名)
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--db-path', default='email_system.db', help='数据库文件路径')
parser.add_argument('--domain', default='mail.example.com', help='服务器域名')
parser.add_argument('--port', type=int, default=5000, help='服务器端口')
args = parser.parse_args()

DB_PATH = args.db_path
SERVER_DOMAIN = args.domain
SERVER_PORT = args.port


# ============ 数据类和枚举 ============

class EmailStatus(Enum):
    """邮件状态"""
    SENT = 'sent'  # 已发送
    RECALLED = 'recalled'  # 已撤回
    READ = 'read'  # 已读


class SecurityLevel(Enum):
    """安全级别"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Attachment:
    """附件信息"""
    filename: str
    content_type: str
    size: int
    data: str  # Base64编码


# ============ 安全防护模块 ============

class SecurityManager:
    """安全管理器 - 处理限流、防爆破等"""

    def __init__(self):
        self.login_attempts: Dict[str, List[datetime.datetime]] = defaultdict(list)
        self.send_attempts: Dict[str, List[datetime.datetime]] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime.datetime] = {}

    def check_login_rate_limit(self, ip: str) -> Tuple[bool, str]:
        """检查登录频率限制"""
        now = datetime.datetime.now()

        # 清理过期记录(1小时内)
        cutoff = now - datetime.timedelta(hours=1)
        self.login_attempts[ip] = [
            t for t in self.login_attempts[ip] if t > cutoff
        ]

        # 检查IP是否被封禁
        if ip in self.blocked_ips:
            if now < self.blocked_ips[ip]:
                remaining = int((self.blocked_ips[ip] - now).total_seconds())
                return False, f"IP被封禁,剩余{remaining}秒"
            else:
                del self.blocked_ips[ip]

        # 5次失败尝试触发限流
        if len(self.login_attempts[ip]) >= 5:
            # 封禁15分钟
            self.blocked_ips[ip] = now + datetime.timedelta(minutes=15)
            return False, "尝试次数过多,账户已被临时封禁15分钟"

        return True, ""

    def record_login_attempt(self, ip: str, success: bool):
        """记录登录尝试"""
        if not success:
            self.login_attempts[ip].append(datetime.datetime.now())

    def check_send_rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """检查发送频率限制(防止DOS)"""
        now = datetime.datetime.now()

        # 清理过期记录(1小时内)
        cutoff = now - datetime.timedelta(hours=1)
        self.send_attempts[user_id] = [
            t for t in self.send_attempts[user_id] if t > cutoff
        ]

        # 每小时最多发送50封邮件
        if len(self.send_attempts[user_id]) >= 50:
            return False, "发送频率过高,请稍后再试"

        # 每分钟最多发送5封邮件
        recent = [t for t in self.send_attempts[user_id]
                 if t > now - datetime.timedelta(minutes=1)]
        if len(recent) >= 5:
            return False, "发送过快,请稍后再试"

        return True, ""

    def record_send_attempt(self, user_id: str):
        """记录发送尝试"""
        self.send_attempts[user_id].append(datetime.datetime.now())


security_manager = SecurityManager()


# ============ 智能分析模块 ============

class IntelligentAnalyzer:
    """智能分析器 - 垃圾邮件识别、快捷回复推荐"""

    # 垃圾邮件关键词
    SPAM_KEYWORDS = [
        '中奖', '优惠', '免费', '点击', '赢取', '奖金',
        '恭喜', '领取', '紧急', '限时', '特价', '促销',
        '中奖通知', '验证码', '退订', 'unsubscribe', 'viagra',
        '百万富翁', '中奖了', '恭喜中奖', '点击领取'
    ]

    # 钓鱼邮件特征
    PHISHING_PATTERNS = [
        r'点击.*验证.*账户',
        r'.*紧急.*登录.*',
        r'.*您的.*账户.*被.*锁定',
        r'.*点击.*取消.*订阅',
        r'win.*prize.*click',
        r'verify.*account.*immediately'
    ]

    # 快捷回复模板
    QUICK_REPLIES = {
        'meeting': '好的,收到。我将在会议中讨论这个议题。',
        'approval': '同意您的提议,请继续推进。',
        'rejection': '抱歉,这个方案目前不太合适,我们需要再讨论一下。',
        'acknowledgment': '收到,谢谢您的邮件。',
        'waiting': '我会尽快处理并给您答复。',
        'thanks': '非常感谢您的帮助!',
        'default': [
            '好的,明白了。',
            '收到,我会尽快处理。',
            '谢谢您的邮件!',
            '已阅读,稍后回复。'
        ]
    }

    @classmethod
    def analyze_spam(cls, subject: str, body: str, sender_id: str) -> Tuple[bool, float, str]:
        """分析是否为垃圾邮件"""
        score = 0.0
        reasons = []

        # 检查标题和正文中的垃圾关键词
        text = f"{subject} {body}".lower()

        for keyword in cls.SPAM_KEYWORDS:
            if keyword.lower() in text:
                score += 0.3
                reasons.append(f"包含敏感词: {keyword}")

        # 检查钓鱼模式
        for pattern in cls.PHISHING_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.5
                reasons.append("疑似钓鱼邮件特征")

        # 检查标题全大写
        if subject.isupper() and len(subject) > 10:
            score += 0.2
            reasons.append("标题全大写")

        # 检查是否包含多个连续的感叹号
        if '!!!' in text or '！！!' in text:
            score += 0.1
            reasons.append("包含过多感叹号")

        # 检查是否包含可疑的URL
        if re.search(r'http[s]?://[^\s]+.*login|verification', text, re.IGNORECASE):
            score += 0.4
            reasons.append("包含可疑登录链接")

        # 阈值判断
        is_spam = score >= 0.7
        return is_spam, score, "; ".join(reasons) if reasons else "正常邮件"

    @classmethod
    def suggest_quick_replies(cls, subject: str, body: str) -> List[str]:
        """建议快捷回复"""
        text = f"{subject} {body}".lower()

        replies = []

        # 根据邮件内容推荐回复
        if '会议' in text or 'meeting' in text.lower():
            replies.append(cls.QUICK_REPLIES['meeting'])
        if '同意' in text or '批准' in text:
            replies.append(cls.QUICK_REPLIES['approval'])
        if '谢谢' in text or '感谢' in text:
            replies.append(cls.QUICK_REPLIES['thanks'])
        if '等待' in text or '回复' in text:
            replies.append(cls.QUICK_REPLIES['waiting'])

        # 默认回复
        if not replies:
            replies = cls.QUICK_REPLIES['default'][:3]

        return replies

    @classmethod
    def extract_quick_actions(cls, body: str) -> List[Dict]:
        """从邮件中提取可执行的快捷操作"""
        actions = []

        # 检测待办事项
        if re.search(r'待办|todo|to[\s-]?do', body, re.IGNORECASE):
            actions.append({
                'type': 'todo',
                'title': '添加到待办',
                'description': '将此邮件添加到待办事项列表'
            })

        # 检测会议邀请
        if re.search(r'会议|meeting|开会', body, re.IGNORECASE):
            actions.append({
                'type': 'calendar',
                'title': '添加到日历',
                'description': '将此会议添加到日历'
            })

        # 检测链接
        links = re.findall(r'https?://[^\s<>"]+', body)
        if links:
            actions.append({
                'type': 'open_link',
                'title': f'打开链接({len(links)}个)',
                'description': '在浏览器中打开邮件中的链接',
                'data': links[0]  # 第一个链接
            })

        # 检测邮件地址
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', body)
        if emails:
            actions.append({
                'type': 'add_contact',
                'title': f'添加联系人({len(emails)}个)',
                'description': '将邮件中的地址添加到联系人'
            })

        return actions


# ============ 加密工具 ============

class CryptoUtils:
    """加密工具类"""

    @staticmethod
    def generate_key_pair() -> Tuple[str, str]:
        """生成 X25519 密钥对"""
        private_key = x25519.X25519PrivateKey.generate()
        public_key = private_key.public_key()

        # 导出公钥(原始格式)
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        # 导出私钥(PKCS8格式)
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        return (
            base64.b64encode(public_bytes).decode(),
            private_bytes.decode()
        )

    @staticmethod
    def derive_shared_secret(private_key_pem: str, public_key_b64: str) -> bytes:
        """使用 ECDH 计算共享密钥"""
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )

        public_bytes = base64.b64decode(public_key_b64)
        public_key = x25519.X25519PublicKey.from_public_bytes(
            public_bytes,
            backend=default_backend()
        )

        return private_key.exchange(public_key)

    @staticmethod
    def encrypt_message(plaintext: str, shared_secret: bytes) -> Dict[str, str]:
        """使用 ChaCha20-Poly1305 加密消息"""
        key = hashlib.sha256(shared_secret).digest()[:32]
        nonce = os.urandom(12)

        cipher = ChaCha20Poly1305(key)
        ciphertext = cipher.encrypt(nonce, plaintext.encode('utf-8'), None)

        return {
            'nonce': base64.b64encode(nonce).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode()
        }

    @staticmethod
    def decrypt_message(encrypted_data: Dict, shared_secret: bytes) -> str:
        """解密消息"""
        key = hashlib.sha256(shared_secret).digest()[:32]

        nonce = base64.b64decode(encrypted_data['nonce'])
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])

        cipher = ChaCha20Poly1305(key)
        plaintext = cipher.decrypt(nonce, ciphertext, None)

        return plaintext.decode('utf-8')

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """使用 PBKDF2 哈希密码"""
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )

        hashed = kdf.derive(password.encode('utf-8'))

        return base64.b64encode(hashed).decode(), salt

    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: bytes) -> bool:
        """验证密码"""
        computed_hash, _ = CryptoUtils.hash_password(password, salt)
        return computed_hash == hashed_password


# ============ 数据库操作 ============

def get_db():
    """获取数据库连接 - 使用WAL模式避免锁定"""
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    # 启用WAL模式以减少锁定
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')  # 30秒超时
    return conn


def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE,
            password_hash TEXT,
            password_salt BLOB,
            public_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')

    # 邮件表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            sender_id TEXT NOT NULL,
            recipient_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            encrypted_body TEXT NOT NULL,
            nonce TEXT NOT NULL,
            read_status BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'sent',
            attachments TEXT,
            spam_score REAL DEFAULT 0.0,
            spam_reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            recalled_at TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(node_id),
            FOREIGN KEY (recipient_id) REFERENCES users(node_id)
        )
    ''')

    # 草稿表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            recipient_id TEXT,
            subject TEXT,
            encrypted_body TEXT,
            attachments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(node_id)
        )
    ''')

    # 联系人表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            contact_node_id TEXT NOT NULL,
            contact_name TEXT,
            contact_public_key TEXT,
            group_name TEXT DEFAULT '未分组',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, contact_node_id),
            FOREIGN KEY (user_id) REFERENCES users(node_id)
        )
    ''')

    # 群组表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            group_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, group_name),
            FOREIGN KEY (user_id) REFERENCES users(node_id)
        )
    ''')

    # 快捷操作记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quick_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            action_data TEXT,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(id),
            FOREIGN KEY (user_id) REFERENCES users(node_id)
        )
    ''')

    # 限流日志表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rate_limit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            ip_address TEXT,
            action TEXT NOT NULL,
            blocked BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_recipient ON emails(recipient_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_groups_user ON groups(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_drafts_user ON drafts(user_id)')

    conn.commit()
    conn.close()

    logger.info(f"数据库初始化完成: {DB_PATH}")


# ============ 认证装饰器 ============

def require_auth(f):
    """认证装饰器"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'success': False, 'error': '未认证'}), 401

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE node_id = ? AND is_active = TRUE',
            (token,)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({'success': False, 'error': '无效的认证'}), 401

        request.user = dict(user)
        request.ip = request.remote_addr
        return f(*args, **kwargs)

    return decorated


# ============ API 端点 ============

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'success': True,
        'status': 'running',
        'architecture': 'CS (Client-Server)',
        'domain': SERVER_DOMAIN,
        'timestamp': datetime.datetime.now().isoformat()
    })


@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        node_id = data.get('node_id')
        username = data.get('username')
        password = data.get('password')
        confirm_password = data.get('confirm_password')

        # 验证参数
        if not node_id:
            return jsonify({'success': False, 'error': '缺少 node_id'}), 400

        if len(node_id) != 40 or not all(c in '0123456789abcdefABCDEF' for c in node_id):
            return jsonify({'success': False, 'error': 'node_id 必须是 40 位十六进制字符'}), 400

        if password and password != confirm_password:
            return jsonify({'success': False, 'error': '两次密码输入不一致'}), 400

        if password and len(password) < 8:
            return jsonify({'success': False, 'error': '密码长度至少8位'}), 400

        # 检查IP限流
        ip = request.remote_addr
        allowed, msg = security_manager.check_login_rate_limit(ip)
        if not allowed:
            return jsonify({'success': False, 'error': msg}), 429

        # 生成密钥对
        public_key, private_key = CryptoUtils.generate_key_pair()

        # 哈希密码
        password_hash = None
        password_salt = None
        if password:
            password_hash, password_salt = CryptoUtils.hash_password(password)

        conn = get_db()
        try:
            cursor = conn.cursor()

            # 检查是否已存在
            existing = cursor.execute(
                'SELECT node_id FROM users WHERE node_id = ?',
                (node_id,)
            ).fetchone()

            if existing:
                return jsonify({'success': False, 'error': '该 node_id 已注册'}), 400

            # 插入新用户
            cursor.execute('''
                INSERT INTO users (node_id, username, password_hash, password_salt, public_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (node_id, username, password_hash, password_salt, public_key))

            conn.commit()

            logger.info(f"用户注册: {node_id[:16]}... ({username})")

            # 返回私钥(仅此一次)
            return jsonify({
                'success': True,
                'message': '注册成功,请保存您的私钥',
                'user': {
                    'node_id': node_id,
                    'username': username,
                    'public_key': public_key
                },
                'private_key': private_key  # 仅返回一次
            })
        finally:
            conn.close()

    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        node_id = data.get('node_id')
        password = data.get('password')

        if not node_id:
            return jsonify({'success': False, 'error': '缺少 node_id'}), 400

        # 检查IP限流
        ip = request.remote_addr
        allowed, msg = security_manager.check_login_rate_limit(ip)
        if not allowed:
            # 记录失败尝试
            security_manager.record_login_attempt(ip, False)
            return jsonify({'success': False, 'error': msg}), 429

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE node_id = ? AND is_active = TRUE',
            (node_id,)
        ).fetchone()

        if not user:
            security_manager.record_login_attempt(ip, False)
            conn.close()
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 验证密码(如果有)
        if user['password_hash']:
            if not password:
                security_manager.record_login_attempt(ip, False)
                conn.close()
                return jsonify({'success': False, 'error': '请输入密码'}), 401

            is_valid = CryptoUtils.verify_password(
                password,
                user['password_hash'],
                user['password_salt']
            )

            if not is_valid:
                security_manager.record_login_attempt(ip, False)
                conn.close()
                return jsonify({'success': False, 'error': '密码错误'}), 401

        # 更新最后在线时间
        conn.execute(
            'UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE node_id = ?',
            (node_id,)
        )
        conn.commit()
        conn.close()

        # 记录成功登录
        security_manager.record_login_attempt(ip, True)

        logger.info(f"用户登录: {node_id[:16]}... ({user['username']})")

        return jsonify({
            'success': True,
            'token': node_id,
            'user': {
                'node_id': user['node_id'],
                'username': user['username'],
                'public_key': user['public_key']
            }
        })

    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/publickey/<node_id>', methods=['GET'])
def get_public_key(node_id):
    """获取用户公钥"""
    try:
        conn = get_db()
        user = conn.execute(
            'SELECT node_id, public_key, username FROM users WHERE node_id = ?',
            (node_id,)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        return jsonify({
            'success': True,
            'node_id': user['node_id'],
            'username': user['username'],
            'public_key': user['public_key']
        })

    except Exception as e:
        logger.error(f"获取公钥失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/inbox', methods=['GET'])
@require_auth
def get_inbox():
    """获取收件箱"""
    try:
        node_id = request.user['node_id']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                e.*,
                u.username as sender_name
            FROM emails e
            LEFT JOIN users u ON e.sender_id = u.node_id
            WHERE e.recipient_id = ? AND e.status = 'sent'
            ORDER BY e.created_at DESC
            LIMIT 100
        ''', (node_id,))

        emails = []
        for row in cursor.fetchall():
            email = dict(row)
            # 智能分析:快捷操作
            if email['encrypted_body']:
                try:
                    # 注意:这里无法解密,只能基于已知的部分内容分析
                    actions = []
                except:
                    actions = []
            else:
                actions = []

            emails.append({
                'id': email['id'],
                'message_id': email['message_id'],
                'sender_id': email['sender_id'],
                'sender_name': email['sender_name'],
                'subject': email['subject'],
                'encrypted_body': email['encrypted_body'],
                'nonce': email['nonce'],
                'read_status': email['read_status'],
                'spam_score': email['spam_score'],
                'spam_reason': email['spam_reason'],
                'attachments': json.loads(email['attachments']) if email['attachments'] else [],
                'created_at': email['created_at'],
                'quick_actions': actions
            })

        conn.close()

        return jsonify({'success': True, 'emails': emails})

    except Exception as e:
        logger.error(f"获取收件箱失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/sent', methods=['GET'])
@require_auth
def get_sent():
    """获取已发送"""
    try:
        node_id = request.user['node_id']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                e.*,
                u.username as recipient_name
            FROM emails e
            LEFT JOIN users u ON e.recipient_id = u.node_id
            WHERE e.sender_id = ?
            ORDER BY e.created_at DESC
            LIMIT 100
        ''', (node_id,))

        emails = []
        for row in cursor.fetchall():
            email = dict(row)
            emails.append({
                'id': email['id'],
                'message_id': email['message_id'],
                'recipient_id': email['recipient_id'],
                'recipient_name': email['recipient_name'],
                'subject': email['subject'],
                'status': email['status'],
                'attachments': json.loads(email['attachments']) if email['attachments'] else [],
                'created_at': email['created_at'],
                'recalled_at': email['recalled_at']
            })

        conn.close()

        return jsonify({'success': True, 'emails': emails})

    except Exception as e:
        logger.error(f"获取已发送失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/drafts', methods=['GET'])
@require_auth
def get_drafts():
    """获取草稿箱"""
    try:
        node_id = request.user['node_id']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM drafts
            WHERE user_id = ?
            ORDER BY updated_at DESC
        ''', (node_id,))

        drafts = []
        for row in cursor.fetchall():
            draft = dict(row)
            drafts.append({
                'id': draft['id'],
                'recipient_id': draft['recipient_id'],
                'subject': draft['subject'],
                'encrypted_body': draft['encrypted_body'],
                'attachments': json.loads(draft['attachments']) if draft['attachments'] else [],
                'created_at': draft['created_at'],
                'updated_at': draft['updated_at']
            })

        conn.close()

        return jsonify({'success': True, 'drafts': drafts})

    except Exception as e:
        logger.error(f"获取草稿箱失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/drafts', methods=['POST'])
@require_auth
def save_draft():
    """保存草稿"""
    try:
        data = request.json
        user_id = request.user['node_id']

        recipient_id = data.get('recipient_id')
        subject = data.get('subject')
        encrypted_body = data.get('encrypted_body')
        attachments = data.get('attachments', [])

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO drafts (user_id, recipient_id, subject, encrypted_body, attachments)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, recipient_id, subject, encrypted_body, json.dumps(attachments)))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '草稿已保存'})

    except Exception as e:
        logger.error(f"保存草稿失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/send', methods=['POST'])
@require_auth
def send_email():
    """发送邮件"""
    try:
        data = request.json
        sender_id = request.user['node_id']

        recipient_id = data.get('recipient_id')
        subject = data.get('subject')
        encrypted_body = data.get('encrypted_body')
        nonce = data.get('nonce')
        attachments = data.get('attachments', [])
        is_bulk = data.get('is_bulk', False)
        bulk_recipients = data.get('bulk_recipients', [])

        # 检查发送频率限制
        allowed, msg = security_manager.check_send_rate_limit(sender_id)
        if not allowed:
            # 记录限流日志
            conn = get_db()
            conn.execute('''
                INSERT INTO rate_limit_logs (user_id, ip_address, action, blocked)
                VALUES (?, ?, ?, TRUE)
            ''', (sender_id, request.ip, 'send_email'))
            conn.commit()
            conn.close()

            return jsonify({'success': False, 'error': msg}), 429

        # 验证参数
        if not subject:
            return jsonify({'success': False, 'error': '缺少主题'}), 400

        if not encrypted_body:
            return jsonify({'success': False, 'error': '缺少邮件内容'}), 400

        recipients = bulk_recipients if is_bulk and bulk_recipients else [recipient_id]

        results = []

        conn = get_db()
        cursor = conn.cursor()

        for recipient in recipients:
            # 生成消息ID
            message_id = hashlib.sha256(
                f"{sender_id}{recipient}{datetime.datetime.now().timestamp()}".encode()
            ).hexdigest()

            # 智能分析:垃圾邮件检测
            is_spam = False
            spam_score = 0.0
            spam_reason = ""
            # 注意:这里无法检测加密内容,可以在发送前由前端检测

            # 插入邮件
            cursor.execute('''
                INSERT INTO emails (message_id, sender_id, recipient_id, subject, encrypted_body, nonce, attachments, spam_score, spam_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                sender_id,
                recipient,
                subject,
                encrypted_body,
                nonce,
                json.dumps(attachments),
                spam_score,
                spam_reason
            ))

            results.append({
                'recipient_id': recipient,
                'message_id': message_id,
                'success': True
            })

        conn.commit()
        conn.close()

        # 记录发送
        security_manager.record_send_attempt(sender_id)

        logger.info(f"邮件发送: {sender_id[:16]}... -> {len(recipients)}位收件人")

        return jsonify({
            'success': True,
            'results': results,
            'message': f'成功发送{len(results)}封邮件'
        })

    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/<int:email_id>/recall', methods=['POST'])
@require_auth
def recall_email(email_id):
    """撤回邮件"""
    try:
        user_id = request.user['node_id']

        conn = get_db()
        cursor = conn.cursor()

        # 检查邮件是否存在且属于当前用户
        email = cursor.execute('''
            SELECT * FROM emails
            WHERE id = ? AND sender_id = ? AND status = 'sent'
        ''', (email_id, user_id)).fetchone()

        if not email:
            conn.close()
            return jsonify({'success': False, 'error': '邮件不存在或无法撤回'}), 404

        # 检查发送时间(5分钟内可撤回)
        email_time = datetime.datetime.fromisoformat(email['created_at'].replace('Z', '+00:00'))
        if datetime.datetime.now() - email_time > datetime.timedelta(minutes=5):
            conn.close()
            return jsonify({'success': False, 'error': '超过5分钟,无法撤回'}), 400

        # 撤回邮件
        cursor.execute('''
            UPDATE emails
            SET status = 'recalled', recalled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (email_id,))

        conn.commit()
        conn.close()

        logger.info(f"邮件撤回: {email_id} by {user_id[:16]}...")

        return jsonify({
            'success': True,
            'message': '邮件已撤回'
        })

    except Exception as e:
        logger.error(f"撤回邮件失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/emails/<int:email_id>/mark-read', methods=['POST'])
@require_auth
def mark_as_read(email_id):
    """标记为已读"""
    try:
        user_id = request.user['node_id']

        conn = get_db()
        conn.execute('''
            UPDATE emails
            SET read_status = TRUE
            WHERE id = ? AND recipient_id = ?
        ''', (email_id, user_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '已标记为已读'})

    except Exception as e:
        logger.error(f"标记已读失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts', methods=['GET'])
@require_auth
def get_contacts():
    """获取联系人列表"""
    try:
        user_id = request.user['node_id']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM contacts
            WHERE user_id = ?
            ORDER BY group_name, created_at DESC
        ''', (user_id,))

        contacts = []
        for row in cursor.fetchall():
            contact = dict(row)
            contacts.append({
                'id': contact['id'],
                'contact_node_id': contact['contact_node_id'],
                'contact_name': contact['contact_name'],
                'group_name': contact['group_name'],
                'created_at': contact['created_at']
            })

        conn.close()

        return jsonify({'success': True, 'contacts': contacts})

    except Exception as e:
        logger.error(f"获取联系人失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts', methods=['POST'])
@require_auth
def add_contact():
    """添加联系人"""
    try:
        user_id = request.user['node_id']
        data = request.json

        contact_node_id = data.get('contact_node_id')
        contact_name = data.get('contact_name')
        group_name = data.get('group_name', '未分组')

        if len(contact_node_id) != 40:
            return jsonify({'success': False, 'error': '节点ID格式错误'}), 400

        conn = get_db()
        recipient = conn.execute(
            'SELECT public_key FROM users WHERE node_id = ?',
            (contact_node_id,)
        ).fetchone()

        if not recipient:
            conn.close()
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contacts (user_id, contact_node_id, contact_name, group_name, contact_public_key)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, contact_node_id, contact_name, group_name, recipient['public_key']))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '联系人添加成功'})

    except Exception as e:
        logger.error(f"添加联系人失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contacts/<int:contact_id>', methods=['DELETE'])
@require_auth
def delete_contact(contact_id):
    """删除联系人"""
    try:
        user_id = request.user['node_id']

        conn = get_db()
        conn.execute('''
            DELETE FROM contacts
            WHERE id = ? AND user_id = ?
        ''', (contact_id, user_id))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '联系人已删除'})

    except Exception as e:
        logger.error(f"删除联系人失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/groups', methods=['GET'])
@require_auth
def get_groups():
    """获取群组列表"""
    try:
        user_id = request.user['node_id']

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT g.*, COUNT(c.id) as contact_count
            FROM groups g
            LEFT JOIN contacts c ON g.user_id = c.user_id AND g.group_name = c.group_name
            WHERE g.user_id = ?
            GROUP BY g.id
        ''', (user_id,))

        groups = []
        for row in cursor.fetchall():
            group = dict(row)
            groups.append({
                'id': group['id'],
                'group_name': group['group_name'],
                'contact_count': group['contact_count'],
                'created_at': group['created_at']
            })

        conn.close()

        return jsonify({'success': True, 'groups': groups})

    except Exception as e:
        logger.error(f"获取群组失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/groups', methods=['POST'])
@require_auth
def create_group():
    """创建群组"""
    try:
        user_id = request.user['node_id']
        data = request.json
        group_name = data.get('group_name')

        if not group_name:
            return jsonify({'success': False, 'error': '缺少群组名称'}), 400

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO groups (user_id, group_name)
            VALUES (?, ?)
        ''', (user_id, group_name))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': '群组创建成功'})

    except Exception as e:
        logger.error(f"创建群组失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/spam', methods=['POST'])
def analyze_spam():
    """分析垃圾邮件(公开API)"""
    try:
        data = request.json
        subject = data.get('subject', '')
        body = data.get('body', '')
        sender_id = data.get('sender_id', 'unknown')

        is_spam, score, reason = IntelligentAnalyzer.analyze_spam(
            subject, body, sender_id
        )

        return jsonify({
            'success': True,
            'is_spam': is_spam,
            'spam_score': score,
            'spam_reason': reason
        })

    except Exception as e:
        logger.error(f"垃圾邮件分析失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/quick-replies', methods=['POST'])
def suggest_replies():
    """建议快捷回复(公开API)"""
    try:
        data = request.json
        subject = data.get('subject', '')
        body = data.get('body', '')

        replies = IntelligentAnalyzer.suggest_quick_replies(subject, body)

        return jsonify({
            'success': True,
            'quick_replies': replies
        })

    except Exception as e:
        logger.error(f"快捷回复推荐失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze/quick-actions', methods=['POST'])
def extract_actions():
    """提取快捷操作(公开API)"""
    try:
        data = request.json
        body = data.get('body', '')

        actions = IntelligentAnalyzer.extract_quick_actions(body)

        return jsonify({
            'success': True,
            'quick_actions': actions
        })

    except Exception as e:
        logger.error(f"快捷操作提取失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============ 主程序 ============

def main():
    """主程序"""
    # 初始化数据库
    init_db()

    logger.info("=" * 60)
    logger.info(f"CS架构邮件系统 - {SERVER_DOMAIN}")
    logger.info("=" * 60)
    logger.info(f"数据库路径: {DB_PATH}")
    logger.info(f"服务端口: {SERVER_PORT}")
    logger.info("")

    # 运行 Flask 应用
    app.run(
        host='0.0.0.0',
        port=SERVER_PORT,
        debug=False
    )


if __name__ == '__main__':
    main()
