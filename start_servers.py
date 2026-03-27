import subprocess
import time
import os

print("=" * 60)
print("启动双服务器邮件系统")
print("=" * 60)

# 清理数据库
db_files = [
    'server_a_data/mail.db',
    'server_b_data/mail.db'
]

for db_file in db_files:
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"✓ 已清理: {db_file}")

# 创建数据目录
os.makedirs('server_a_data', exist_ok=True)
os.makedirs('server_b_data', exist_ok=True)

print("\n正在启动服务器A (端口 5001)...")
process_a = subprocess.Popen([
    'python', 'mail_server.py',
    '--db-path', 'server_a_data/mail.db',
    '--domain', 'mail-a.com',
    '--port', '5001'
])

time.sleep(3)

print("正在启动服务器B (端口 5002)...")
process_b = subprocess.Popen([
    'python', 'mail_server.py',
    '--db-path', 'server_b_data/mail.db',
    '--domain', 'mail-b.com',
    '--port', '5002'
])

time.sleep(3)

print("\n" + "=" * 60)
print("✓ 双服务器已启动!")
print("=" * 60)
print(f"  服务器A: http://localhost:5001")
print(f"  服务器B: http://localhost:5002")
print("\n按 Ctrl+C 停止所有服务器")
print("=" * 60)

try:
    # 等待进程
    process_a.wait()
    process_b.wait()
except KeyboardInterrupt:
    print("\n正在停止服务器...")
    process_a.terminate()
    process_b.terminate()
    process_a.wait()
    process_b.wait()
    print("✓ 服务器已停止")
