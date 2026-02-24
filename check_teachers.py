from app import app, db, User

with app.app_context():
    # 查询所有教师账号
    teachers = User.query.filter_by(role='teacher').all()
    print(f"Found {len(teachers)} teachers:")
    for teacher in teachers:
        print(f"  - {teacher.username} (ID: {teacher.id}, Email: {teacher.email})")
    
    # 检查是否有5个教师账号
    if len(teachers) == 5:
        print("✅ All 5 teacher accounts have been created successfully!")
    else:
        print("❌ Expected 5 teacher accounts, but found", len(teachers))
