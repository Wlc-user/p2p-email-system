"""
清理测试数据库
"""
import os
import shutil

def clean_databases():
    """清理所有测试数据库"""
    db_files = [
        'server_a_data/mail.db',
        'server_b_data/mail.db',
        'email_system.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"[OK] 已删除: {db_file}")
            except Exception as e:
                print(f"[ERROR] 删除失败 {db_file}: {e}")
        else:
            print(f"[SKIP] 不存在: {db_file}")

if __name__ == '__main__':
    print("=" * 60)
    print("清理测试数据库")
    print("=" * 60)
    clean_databases()
    print("=" * 60)
    print("完成!")
    print("=" * 60)
