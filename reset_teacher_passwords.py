from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    print("开始重置教师密码...")

    teachers = ['teacherA', 'teacherB', 'teacherC', 'teacherD', 'teacherE']
    new_password = '666888'
    hashed_pwd = generate_password_hash(new_password, method='pbkdf2:sha256')

    print(f"新密码: {new_password}")
    print(f"哈希值: {hashed_pwd[:50]}...")

    for username in teachers:
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"\n找到教师: {username}")
            print(f"当前密码: {user.password[:50] if user.password else 'None'}...")

            # 更新密码
            user.password = hashed_pwd
            print(f"已更新密码")
        else:
            print(f"\n❌ 教师 {username} 不存在")

    try:
        db.session.commit()
        print("\n✅ 所有教师密码已重置为 '666888'")

        # 验证
        print("\n验证密码:")
        for username in teachers:
            user = User.query.filter_by(username=username).first()
            if user:
                from werkzeug.security import check_password_hash

                is_correct = check_password_hash(user.password, '666888')
                print(f"{username}: {'✅ 密码正确' if is_correct else '❌ 密码错误'}")

    except Exception as e:
        print(f"\n❌ 提交失败: {str(e)}")
        db.session.rollback()