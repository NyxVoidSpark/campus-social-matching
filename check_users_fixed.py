from app import app, db, User

with app.app_context():
    users = User.query.all()

    if not users:
        print("数据库中没有用户")
    else:
        print("=== 注册用户列表 ===")

        # 获取第一个用户的所有属性，了解数据结构
        if users:
            first_user = users[0]
            print("可用的用户字段:")
            for attr in dir(first_user):
                if not attr.startswith('_') and not callable(getattr(first_user, attr)):
                    print(f"  - {attr}")
            print("-" * 50)

        # 显示所有用户（只显示安全字段）
        for i, user in enumerate(users, 1):
            print(f"用户 {i}:")
            print(f"  ID: {getattr(user, 'id', 'N/A')}")
            print(f"  用户名: {getattr(user, 'username', 'N/A')}")
            print(f"  邮箱: {getattr(user, 'email', 'N/A')}")

            # 尝试获取常用字段
            for field in ['real_name', 'student_id', 'major', 'hobbies', 'bio', 'gender', 'grade']:
                if hasattr(user, field):
                    value = getattr(user, field)
                    if value:
                        print(f"  {field}: {value}")

            print(f"  头像: {getattr(user, 'avatar', 'N/A')}")
            print(f"  注册时间: {getattr(user, 'created_at', 'N/A')}")
            print("-" * 50)

        print(f"\n总用户数: {len(users)}")