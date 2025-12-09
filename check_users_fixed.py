from app import app, db, User

with app.app_context():
    users = User.query.all()

    if not users:
        print("数据库中没有用户")
    else:
        print("=== 注册用户列表 ===")
        for user in users:
            print(f"ID: {user.id}")
            print(f"  用户名: {user.username}")
            print(f"  邮箱: {user.email}")
            print(f"  真实姓名: {user.real_name or '未设置'}")
            print(f"  学号: {user.student_id or '未设置'}")
            print(f"  专业: {user.major or '未设置'}")
            print(f"  兴趣: {user.interests or '未设置'}")
            print(f"  头像: {user.avatar}")
            print(f"  注册时间: {user.created_at}")
            print("-" * 50)

        print(f"\n总用户数: {len(users)}")