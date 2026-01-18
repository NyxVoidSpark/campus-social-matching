from app import app, db, User
from werkzeug.security import generate_password_hash
import os

with app.app_context():
    db.create_all()

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)

    # 初始化5个教师账号（如果不存在）
    teacher_usernames = ['teacherA', 'teacherB', 'teacherC', 'teacherD', 'teacherE']
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
    db.session.commit()

print("Database initialized successfully")