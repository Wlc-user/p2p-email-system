"""简单测试 - 修复后的API路径测试"""
import requests

SERVER_A = 'http://localhost:5001'

def test_fixed_apis():
    """测试修复后的API路径"""
    print("=== 测试修复后的API路径 ===")
    
    # 测试1: 健康检查
    print("\n1. 健康检查...")
    resp = requests.get(f'{SERVER_A}/api/health')
    print(f"   状态: {resp.status_code}")
    print(f"   响应: {resp.json()}")
    
    # 测试2: 注册用户
    print("\n2. 注册用户...")
    import random
    unique_id = ''.join(random.choices('0123456789abcdef', k=40))
    node_id = unique_id
    username = f'Alice_{random.randint(1000, 9999)}'
    resp = requests.post(f'{SERVER_A}/api/register', json={
        'node_id': node_id,
        'username': username,
        'password': 'alice123',
        'confirm_password': 'alice123'
    })
    print(f"   状态: {resp.status_code}")
    print(f"   响应: {resp.json()}")
    
    # 测试3: 登录
    print("\n3. 登录...")
    resp = requests.post(f'{SERVER_A}/api/login', json={
        'node_id': node_id,
        'password': 'alice123'
    })
    print(f"   状态: {resp.status_code}")
    resp_data = resp.json()
    print(f"   响应: {resp_data}")
    if resp_data.get('success'):
        token = resp_data.get('token', node_id)
    
    # 测试4: 垃圾邮件分析
    print("\n4. 垃圾邮件分析...")
    resp = requests.post(f'{SERVER_A}/api/analyze/spam', json={
        'subject': '恭喜中奖!!!',
        'body': '点击领取100万大奖!!!限时优惠!!!'
    })
    print(f"   状态: {resp.status_code}")
    print(f"   响应: {resp.json()}")
    
    # 测试5: AI快捷回复 (修复后的路径)
    print("\n5. AI快捷回复...")
    resp = requests.post(f'{SERVER_A}/api/analyze/quick-replies', json={
        'subject': '会议通知',
        'body': '明天下午3点开会,请准时参加。'
    })
    print(f"   状态: {resp.status_code}")
    print(f"   响应: {resp.json()}")
    
    print("\n=== 所有API测试完成 ===")

if __name__ == '__main__':
    test_fixed_apis()
