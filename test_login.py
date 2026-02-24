import requests

# 测试登录接口
def test_login():
    url = 'http://127.0.0.1:5001/api/login'
    
    # 测试教师账号登录
    test_cases = [
        {'username': 'teacherA', 'password': '666888', 'expected_success': True},
        {'username': 'teacherB', 'password': '666888', 'expected_success': True},
        {'username': 'teacherC', 'password': '666888', 'expected_success': True},
        {'username': 'teacherD', 'password': '666888', 'expected_success': True},
        {'username': 'teacherE', 'password': '666888', 'expected_success': True},
        {'username': 'teacherA', 'password': 'wrongpassword', 'expected_success': False},
        {'username': 'nonexistent', 'password': '666888', 'expected_success': False},
    ]
    
    for test_case in test_cases:
        data = {
            'username': test_case['username'],
            'password': test_case['password']
        }
        
        response = requests.post(url, json=data, allow_redirects=False)
        result = response.json()
        
        print(f"测试账号: {test_case['username']}")
        print(f"密码: {test_case['password']}")
        print(f"响应: {result}")
        print(f"期望成功: {test_case['expected_success']}")
        print(f"实际成功: {result.get('success', False)}")
        print(f"测试结果: {'通过' if result.get('success') == test_case['expected_success'] else '失败'}")
        print('-' * 50)

if __name__ == '__main__':
    test_login()
