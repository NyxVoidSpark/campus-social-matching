from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 数据库配置 - 替换下面的密码为你自己设置的MySQL root密码
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:04822211858@localhost/college_platform?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)

# 定义数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(200), default='static/avatars/default.jpg')
    major = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activity_id = db.Column(db.Integer, db.ForeignKey('activity.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

# 教学信息模型
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(50))
    time = db.Column(db.String(50))
    location = db.Column(db.String(100))
    type = db.Column(db.String(20), default='课程')

# 生活服务信息模型
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text)
    time = db.Column(db.String(50))
    type = db.Column(db.String(20), default='后勤')

# 科研信息模型
class Research(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    deadline = db.Column(db.String(50))
    organizer = db.Column(db.String(50))
    type = db.Column(db.String(20), default='科研竞赛')

# 关注关系模型
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# 创建所有表
def create_tables():
    with app.app_context():
        db.create_all()
        print("✅ 数据库表创建成功！")
        print("📊 已创建的表：")
        print("- users (用户表)")
        print("- activities (活动表)") 
        print("- comments (评论表)")
        print("- courses (教学信息表)")
        print("- services (生活服务表)")
        print("- researches (科研信息表)")
        print("- follows (关注关系表)")

if __name__ == '__main__':
    create_tables()