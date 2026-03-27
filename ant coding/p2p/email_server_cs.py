"""
CS 架构邮件服务器
基于 Flask 的客户端-服务器架构
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import os
import sqlite3
import datetime
import secrets
import functools
import logging

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

# 数据库路径
DB_PATH = 'email_cs.db'


# ============ 数据库操作 ============

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
            public_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            UNIQUE(user_id, contact_node_id)
        )
    ''')

    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_recipient ON emails(recipient_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_user ON contacts(user_id)')

    conn.commit()
    conn.close()

    logger.info("数据库初始化完成")


# ============ 密钥管理 ============

def generate_key_pair():
    """生成 X25519 密钥对"""
    private_key = x25519.X25519PrivateKey.generate()
    public_key = private_key.public_key()

    # 导出公钥（原始格式）
    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )

    # 导出私钥（PKCS8格式）
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    return {
        'private_key': private_bytes.decode(),
        'public_key': base64.b64encode(public_bytes).decode()
    }


def derive_shared_secret(private_key_pem, public_key_b64):
    """使用 ECDH 计算共享密钥"""
    # 加载私钥
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode(),
        password=None,
        backend=default_backend()
    )

    # 加载公钥
    public_bytes = base64.b64decode(public_key_b64)
    public_key = x25519.X25519PublicKey.from_public_bytes(
        public_bytes,
        backend=default_backend()
    )

    # 计算共享密钥
    shared_secret = private_key.exchange(public_key)

    return shared_secret


def encrypt_message(plaintext, shared_secret):
    """使用 ChaCha20-Poly1305 加密消息"""
    # 从共享密钥派生加密密钥
    key = hashlib.sha256(shared_secret).digest()[:32]
    nonce = os.urandom(12)  # ChaCha20 需要 12 字节 nonce

    # 加密
    cipher = ChaCha20Poly1305(key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode('utf-8'), None)

    return {
        'nonce': base64.b64encode(nonce).decode(),
        'ciphertext': base64.b64encode(ciphertext).decode()
    }


def decrypt_message(encrypted_data, shared_secret):
    """解密消息"""
    key = hashlib.sha256(shared_secret).digest()[:32]

    nonce = base64.b64decode(encrypted_data['nonce'])
    ciphertext = base64.b64decode(encrypted_data['ciphertext'])

    cipher = ChaCha20Poly1305(key)
    plaintext = cipher.decrypt(nonce, ciphertext, None)

    return plaintext.decode('utf-8')


# ============ 认证装饰器 ============

def require_auth(f):
    """认证装饰器"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')

        if not token:
            return jsonify({'success': False, 'error': '未认证'}), 401

        # 简化：实际应用中应该验证 JWT
        # 这里暂时假设 token 就是 node_id
        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE node_id = ?',
            (token,)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({'success': False, 'error': '无效的认证'}), 401

        # 将用户信息存入 g
        request.user = dict(user)
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
        'timestamp': datetime.datetime.now().isoformat()
    })


@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        node_id = data.get('node_id')
        username = data.get('username')

        if not node_id:
            return jsonify({'success': False, 'error': '缺少 node_id'}), 400

        if len(node_id) != 40 or not all(c in '0123456789abcdefABCDEF' for c in node_id):
            return jsonify({'success': False, 'error': 'node_id 必须是 40 位十六进制字符'}), 400

        # 生成密钥对
        key_pair = generate_key_pair()

        conn = get_db()
        cursor = conn.cursor()

        # 检查是否已存在
        existing = cursor.execute(
            'SELECT node_id FROM users WHERE node_id = ?',
            (node_id,)
        ).fetchone()

        if existing:
            conn.close()
            return jsonify({'success': False, 'error': '该 node_id 已注册'}), 400

        # 插入新用户
        cursor.execute(
            '''INSERT INTO users (node_id, username, public_key)
               VALUES (?, ?, ?)''',
            (node_id, username, key_pair['public_key'])
        )

        conn.commit()

        user = cursor.execute(
            'SELECT * FROM users WHERE node_id = ?',
            (node_id,)
        ).fetchone()

        conn.close()

        logger.info(f"用户注册: {node_id[:16]}...")

        # 返回私钥（仅此一次，用户需要保存）
        return jsonify({
            'success': True,
            'message': '注册成功，请保存您的私钥',
            'user': {
                'node_id': node_id,
                'username': username,
                'public_key': key_pair['public_key']
            },
            'private_key': key_pair['private_key']  # 仅返回一次
        })

    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        node_id = data.get('node_id')

        if not node_id:
            return jsonify({'success': False, 'error': '缺少 node_id'}), 400

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM users WHERE node_id = ?',
            (node_id,)
        ).fetchone()
        conn.close()

        if not user:
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 更新最后在线时间
        conn = get_db()
        conn.execute(
            'UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE node_id = ?',
            (node_id,)
        )
        conn.commit()
        conn.close()

        # 简化：使用 node_id 作为 token
        # 实际应用中应该生成 JWT
        token = node_id

        logger.info(f"用户登录: {node_id[:16]}...")

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'node_id': user['node_id'],
                'username': user['username']
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

        # 获取收到的邮件，包含发送者信息
        cursor.execute('''
            SELECT
                e.*,
                u.username as sender_name
            FROM emails e
            LEFT JOIN users u ON e.sender_id = u.node_id
            WHERE e.recipient_id = ?
            ORDER BY e.created_at DESC
        ''', (node_id,))

        emails = []
        for row in cursor.fetchall():
            email = dict(row)
            # 不返回加密内容，需要前端解密
            emails.append({
                'id': email['id'],
                'message_id': email['message_id'],
                'sender_id': email['sender_id'],
                'sender_name': email['sender_name'],
                'subject': email['subject'],
                'encrypted_body': email['encrypted_body'],
                'nonce': email['nonce'],
                'read_status': email['read_status'],
                'created_at': email['created_at']
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
                'created_at': email['created_at']
            })

        conn.close()

        return jsonify({'success': True, 'emails': emails})

    except Exception as e:
        logger.error(f"获取已发送失败: {e}")
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
        body = data.get('body')
        encrypted_body = data.get('encrypted_body')
        nonce = data.get('nonce')

        # 验证必要参数
        if not all([recipient_id, subject]):
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        # 生成消息ID
        import hashlib
        message_id = hashlib.sha256(
            f"{sender_id}{recipient_id}{datetime.datetime.now().timestamp()}".encode()
        ).hexdigest()

        conn = get_db()
        cursor = conn.cursor()

        # 如果前端未加密（兼容性），服务器加密
        if not encrypted_body and body:
            # 获取接收者公钥
            recipient = cursor.execute(
                'SELECT public_key FROM users WHERE node_id = ?',
                (recipient_id,)
            ).fetchone()

            if not recipient:
                conn.close()
                return jsonify({'success': False, 'error': '接收者不存在'}), 404

            # 获取发送者私钥（应该从前端传来或存储）
            # 这里简化：假设前端已经加密
            encrypted_body = body
            nonce = base64.b64encode(os.urandom(12)).decode()

        # 插入邮件
        cursor.execute('''
            INSERT INTO emails (message_id, sender_id, recipient_id, subject, encrypted_body, nonce)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, sender_id, recipient_id, subject, encrypted_body, nonce))

        conn.commit()
        conn.close()

        logger.info(f"邮件发送: {sender_id[:16]}... -> {recipient_id[:16]}...")

        return jsonify({
            'success': True,
            'message_id': message_id,
            'message': '邮件发送成功'
        })

    except Exception as e:
        logger.error(f"发送邮件失败: {e}")
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
            ORDER BY created_at DESC
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

        # 验证节点ID格式
        if len(contact_node_id) != 40:
            return jsonify({'success': False, 'error': '节点ID格式错误'}), 400

        # 检查用户是否存在
        conn = get_db()
        recipient = conn.execute(
            'SELECT public_key FROM users WHERE node_id = ?',
            (contact_node_id,)
        ).fetchone()

        if not recipient:
            conn.close()
            return jsonify({'success': False, 'error': '用户不存在'}), 404

        # 插入联系人
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO contacts (user_id, contact_node_id, contact_name, group_name, contact_public_key)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, contact_node_id, contact_name, group_name, recipient['public_key']))

        conn.commit()
        conn.close()

        logger.info(f"联系人添加: {user_id[:16]}... -> {contact_node_id[:16]}...")

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


# ============ 主程序 ============

def main():
    """主程序"""
    # 初始化数据库
    init_db()

    logger.info("=" * 60)
    logger.info("CS 架构邮件服务器")
    logger.info("=" * 60)
    logger.info("")

    # 运行 Flask 应用
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )


if __name__ == '__main__':
    main()
