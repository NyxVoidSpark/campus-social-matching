from app import app, db, User
from werkzeug.security import generate_password_hash
import os
import sqlite3

print("开始初始化数据库...")
print(f"当前目录: {os.getcwd()}")
print(f"数据库文件: campus_social.db")

with app.app_context():
    try:
        # 检查数据库连接
        print("正在创建数据库表...")
        db.create_all()
        print("✅ 数据库表创建成功")

        # 确保上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
        print("✅ 上传目录创建成功")

        # 检查用户表是否存在
        conn = sqlite3.connect('campus_social.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        user_table = cursor.fetchone()
        print(f"用户表存在: {user_table is not None}")
        conn.close()

        # 初始化5个教师账号（如果不存在）
        print("正在初始化教师账号...")
        teacher_usernames = ['teacherA', 'teacherB', 'teacherC', 'teacherD', 'teacherE']
        created_count = 0
        for username in teacher_usernames:
            if not User.query.filter_by(username=username).first():
                hashed_pwd = generate_password_hash('666888', method='pbkdf2:sha256')
                teacher = User(
                    username=username,
                    email=f"{username}@school.com",
                    password=hashed_pwd,
                    role='teacher',
                    real_name=username,
                    bio=f"官方认证教师-{username}"
                )
                db.session.add(teacher)
                created_count += 1
        
        if created_count > 0:
            db.session.commit()
            print(f"✅ 成功创建 {created_count} 个教师账号")
        else:
            print("✅ 教师账号已存在，无需创建")

        # 验证教师账号
        print("验证教师账号...")
        teachers = User.query.filter_by(role='teacher').all()
        print(f"教师账号数量: {len(teachers)}")
        for teacher in teachers:
            print(f"  - {teacher.username}")

    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()

print("Database initialized successfully")