"""简单测试脚本"""
import requests
import json
import secrets

SERVER = 'http://localhost:5001'

def test():
    print("开始测试...")
    
    # 1. 注册
    node_id = secrets.token_hex(20)
    print(f"Node ID: {node_id}")
    
    data = {
        'node_id': node_id,
        'username': f'TestUser_{int(time.time())}',
        'password': 'test123456',
        'confirm_password': 'test123456'
    }
    
    resp = requests.post(f'{SERVER}/api/register', json=data)
    result = resp.json()
    print(f"注册结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if not result.get('success'):
        print("注册失败")
        return False
    
    # 保存私钥
    private_key = result['private_key']
    token = result.get('token', '')
    print(f"Token: {token[:50] if token else 'N/A'}...")
    
    # 2. 登录
    login_data = {
        'node_id': node_id,
        'password': 'test123456'
    }
    
    resp = requests.post(f'{SERVER}/api/login', json=login_data)
    result = resp.json()
    print(f"登录结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get('success'):
        token = result['token']
        print(f"登录成功, Token: {token[:50]}...")
    
    print("\n测试完成!")
    return True

if __name__ == '__main__':
    import time
    test()
