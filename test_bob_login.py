"""测试Bob登录问题修复"""
import requests
import random

SERVER_A = 'http://localhost:5001'

# 生成随机用户
random_id = ''.join(random.choices('0123456789abcdef', k=40))
bob_username = f'Bob_{random.randint(1000, 9999)}'
bob_password = 'bob12345'

print("=== 测试Bob登录修复 ===")

# 1. 注册Bob
print("\n1. 注册Bob...")
resp = requests.post(f'{SERVER_A}/api/register', json={
    'node_id': random_id,
    'username': bob_username,
    'password': bob_password,
    'confirm_password': bob_password
})
print(f"注册状态: {resp.status_code}")
print(f"响应: {resp.json()}")

# 2. 登录Bob（带密码）
print("\n2. 登录Bob（带密码）...")
resp = requests.post(f'{SERVER_A}/api/login', json={
    'node_id': random_id,
    'password': bob_password
})
print(f"登录状态: {resp.status_code}")
resp_data = resp.json()
print(f"响应: {resp_data}")

if resp_data.get('success'):
    token = resp_data.get('token')
    print(f"[OK] 登录成功! Token: {token[:16]}...")
else:
    print(f"[FAIL] 登录失败: {resp_data.get('error')}")

print("\n=== 测试完成 ===")
