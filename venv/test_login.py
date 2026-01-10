# test_login.py - 放在项目根目录
import requests
import json
import sys


def test_teacher_login():
    """测试教师账号登录"""
    print("=== 教师账号登录测试 ===\n")

    # 教师账号列表
    teachers = ['teacherA', 'teacherB', 'teacherC', 'teacherD', 'teacherE']
    password = '666888'
    base_url = "http://localhost:5001"

    success_count = 0

    for teacher in teachers:
        print(f"🔧 测试登录: {teacher}")

        url = f"{base_url}/api/login"
        data = {
            "username": teacher,
            "password": password
        }

        try:
            response = requests.post(url, json=data, timeout=5)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ 登录成功!")
                    print(f"  用户ID: {result['data'].get('user_id')}")
                    print(f"  角色: {result['data'].get('role')}")
                    success_count += 1
                else:
                    print(f"  ❌ 登录失败: {result.get('error')}")
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")
                print(f"  响应: {response.text[:200]}")

        except requests.exceptions.ConnectionError:
            print("  ❌ 连接失败 - 确保服务器正在运行 (python app.py)")
            print("  请先运行: python app.py")
            break
        except Exception as e:
            print(f"  ❌ 请求异常: {str(e)}")

    print(f"\n=== 测试完成 ===")
    print(f"成功登录: {success_count}/{len(teachers)}")

    return success_count == len(teachers)


def test_student_login():
    """测试学生账号登录"""
    print("\n=== 测试学生账号 ===")

    # 您需要知道学生账号的密码
    student_accounts = [
        {"username": "fujia", "password": "您知道的密码"},
        {"username": "fujiahui", "password": "您知道的密码"}
    ]

    base_url = "http://localhost:5001"

    for account in student_accounts:
        if not account["password"] or account["password"] == "您知道的密码":
            continue

        print(f"\n测试登录: {account['username']}")

        url = f"{base_url}/api/login"
        data = {
            "username": account["username"],
            "password": account["password"]
        }

        try:
            response = requests.post(url, json=data, timeout=5)
            print(f"  状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"  ✅ 登录成功!")
                else:
                    print(f"  ❌ 登录失败: {result.get('error')}")
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")

        except Exception as e:
            print(f"  ❌ 请求异常: {str(e)}")


if __name__ == "__main__":
    # 检查服务器是否运行
    print("检查服务器连接...")
    try:
        response = requests.get("http://localhost:5001", timeout=3)
        print("服务器正在运行\n")
    except:
        print("\n⚠️  警告: 服务器可能未运行")
        print("请先启动服务器: python app.py")
        print("是否继续测试？(y/n): ", end="")
        choice = input().strip().lower()
        if choice != 'y':
            sys.exit(1)
        print()

    # 运行测试
    test_teacher_login()
    # test_student_login()  # 如果您知道学生密码，可以取消注释