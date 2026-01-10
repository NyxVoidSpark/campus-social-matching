from app import app, db, User
with app.app_context():
    users = User.query.all()
    if not users:
        print("数据库中没有用户")
    else:
        print("=== 注册用户列表 ===")
        # 明确指定需要显示的字段（避免遍历内部属性）
        display_fields = ['id', 'username', 'email', 'real_name', 'student_id',
                          'major', 'hobbies', 'bio', 'gender', 'grade', 'avatar', 'created_at']
        print("可用的用户字段:", ', '.join(display_fields))
        print("-" * 50)
        # 显示所有用户
        for i, user in enumerate(users, 1):
            print(f"用户 {i}:")
            for field in display_fields:
                value = getattr(user, field, 'N/A')
                # 只显示非空值（避免冗余）
                if value and value != '':
                    print(f"  {field}: {value}")
            print("-" * 50)
        print(f"\n总用户数: {len(users)}")