from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from werkzeug.utils import secure_filename
import json
from difflib import SequenceMatcher
from flask_migrate import Migrate
from functools import wraps

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5001", "http://127.0.0.1:5001"])  # 明确指定允许的来源
app.secret_key = 'campus_social_2025'  # 用于session加密
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7  # Session有效期7天

# MySQL数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER', 'root')}:{os.getenv('MYSQL_PASSWORD', '123456')}@"
    f"{os.getenv('MYSQL_HOST', 'localhost')}:{os.getenv('MYSQL_PORT', '3306')}/{os.getenv('MYSQL_DB', 'campus_social')}?charset=utf8mb4"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 添加配置文件上传
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  # 20MB 限制
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 扩展允许类型：图片/视频/文档/压缩包
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'pdf', 'docx', 'pptx', 'xlsx', 'zip'}

# 初始化数据库
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # 绑定app和db

# ---------------------------- 数据库模型（整合后） ----------------------------

class User(db.Model):
    id = db.Column(db.String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8])  # 兼容UUID格式
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    hobbies = db.Column(db.String(200))  # 兴趣标签
    major = db.Column(db.String(100))  # 专业/部门
    grade = db.Column(db.String(20))  # 年级/职称
    
    # 扩展字段
    real_name = db.Column(db.String(50), default='')  # 真实姓名
    student_id = db.Column(db.String(20), default='')  # 学号/工号
    phone = db.Column(db.String(11), default='')  # 手机号
    gender = db.Column(db.String(10), default='')  # 性别
    bio = db.Column(db.String(200), default='')  # 个人简介
    avatar = db.Column(db.String(200), default='/static/images/default.jpg')  # 头像
    role = db.Column(db.String(20), default='student')  # 身份（student/teacher）
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # 创建时间

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 学术/体育/艺术/其他
    time = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    tags = db.Column(db.String(200), default='')  # 活动标签，逗号分隔
    description = db.Column(db.Text, default='')  # 活动描述
    initiator_id = db.Column(db.String(8), db.ForeignKey('user.id'))  # 发起人ID
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # 创建时间
    
    # 扩展支持：人数上限、费用、报名截止、活动状态与签到二维码令牌
    participants_limit = db.Column(db.Integer, nullable=True)
    fee = db.Column(db.String(50), default='')
    signup_deadline = db.Column(db.String(50), default='')
    status = db.Column(db.String(30), default='upcoming')  # upcoming / ongoing / finished / cancelled
    participant_count = db.Column(db.Integer, default=0)  # 参与人数，默认0
    qr_token = db.Column(db.String(64), unique=True, nullable=True)
    
    # 关联参与者
    participants = db.relationship('User', secondary='activity_participants',
                                   backref=db.backref('joined_activities'))

# 活动-用户多对多关联表（报名关系）
activity_participants = db.Table(
    'activity_participants',
    db.Column('user_id', db.String(8), db.ForeignKey('user.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True)
)

# 收藏关系表
activity_favorites = db.Table(
    'activity_favorites',
    db.Column('user_id', db.String(8), db.ForeignKey('user.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True)
)

# 给User添加收藏关联
User.favorite_activities = db.relationship('Activity', secondary=activity_favorites, backref=db.backref('favorited_by'))

# 关注关系表
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='_follower_followed_uc'),)

# 好友关系表
class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending: 待处理, accepted: 已接受, rejected: 已拒绝
    requester_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)  # 发起请求的用户ID
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    __table_args__ = (db.UniqueConstraint('user1_id', 'user2_id', name='_user1_user2_uc'),)

# 消息表
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ---------------------------- 帖子与审核相关模型 ----------------------------

# 栏目
POST_CATEGORIES = [
    "教学科研",
    "校园活动",
    "生活服务",
    "求职就业",
    "学术交流",
    "兴趣社群",
    "求助问答",
    "校园资讯"
]

# 模板定义（前端展示用）
POST_TEMPLATES = {
    '教学科研': {
        'fields': [
            {'name': 'course_code', 'label': '课程号', 'type': 'text', 'required': False},
            {'name': 'teacher', 'label': '教师姓名', 'type': 'text', 'required': False},
            {'name': 'credit_ack', 'label': '学分认定', 'type': 'checkbox', 'required': False}
        ]
    },
    '校园活动': {
        'fields': [
            {'name': 'time', 'label': '时间', 'type': 'text', 'required': True},
            {'name': 'location', 'label': '地点', 'type': 'text', 'required': True},
            {'name': 'participants_limit', 'label': '人数上限', 'type': 'number', 'required': False},
            {'name': 'fee', 'label': '费用', 'type': 'text', 'required': False},
            {'name': 'signup_link', 'label': '报名链接', 'type': 'text', 'required': False}
        ]
    },
    '生活服务': {
        'fields': [
            {'name': 'trade_type', 'label': '交易类型', 'type': 'text', 'required': False}
        ]
    },
    '求职就业': {
        'fields': [
            {'name': 'company', 'label': '企业名称', 'type': 'text', 'required': False},
            {'name': 'enterprise_certified', 'label': '企业认证', 'type': 'checkbox', 'required': False}
        ]
    },
    '兴趣社群': {
        'fields': [
            {'name': 'group_name', 'label': '兴趣组名', 'type': 'text', 'required': False}
        ]
    },
    '互助问答': {
        'fields': [
            {'name': 'reward_points', 'label': '悬赏积分', 'type': 'number', 'required': False},
            {'name': 'anonymous', 'label': '匿名发布', 'type': 'checkbox', 'required': False}
        ]
    },
    '校园资讯': {
        'fields': [
            {'name': 'scope', 'label': '推送范围', 'type': 'text', 'required': False},
            {'name': 'pin', 'label': '置顶', 'type': 'checkbox', 'required': False}
        ]
    }
}

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, default='')
    is_markdown = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(200), default='')
    media = db.Column(db.Text, default='')  # JSON list: [{'url':..., 'filename':...}, ...]
    metadata_json = db.Column(db.Text, default='')  # JSON for template fields
    author_id = db.Column(db.String(8), db.ForeignKey('user.id'))
    is_official = db.Column(db.Boolean, default=False)
    org_name = db.Column(db.String(120), default='')
    review_status = db.Column(db.String(20), default='pending')  # 审核状态（pending/approved/rejected）
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 帖子审核记录表
class PostReview(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    teacher_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending/approved/rejected
    comment = db.Column(db.String(200), default='')
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 给Post添加审核关联
Post.reviews = db.relationship('PostReview', backref='post', cascade='all, delete-orphan')

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    creator_id = db.Column(db.String(8), db.ForeignKey('user.id'))
    # 小组类型：public / review / private
    type = db.Column(db.String(20), default='public')
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 小组成员多对多
group_members = db.Table(
    'group_members',
    db.Column('user_id', db.String(8), db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

# 小组加入申请
class MembershipRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    message = db.Column(db.String(300), default='')
    status = db.Column(db.String(20), default='pending')  # pending / approved / rejected
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 评论（支持楼中楼）
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 反应/互动（点赞/收藏/转发/有用/打赏等）
class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    type = db.Column(db.String(30), nullable=False)  # like, favorite, repost, useful, unuseful, reward
    metadata_json = db.Column(db.String(200), default='')
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 组队招募
class TeamRecruit(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    skills = db.Column(db.String(200), default='')  # 逗号分隔的技能标签
    time_frame = db.Column(db.String(100), default='')
    creator_id = db.Column(db.String(8), db.ForeignKey('user.id'))
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 组队成员多对多
team_members = db.Table(
    'team_members',
    db.Column('user_id', db.String(8), db.ForeignKey('user.id'), primary_key=True),
    db.Column('team_id', db.Integer, db.ForeignKey('team_recruit.id'), primary_key=True)
)

# 积分流水记录
class PointsLedger(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    change = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), default='')
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# 给 User 添加常用关系属性
User.groups = db.relationship('Group', secondary=group_members, backref=db.backref('members'))

# ---------------------------- 辅助函数 ----------------------------

def find_user(username):
    """根据用户名查找用户"""
    return User.query.filter_by(username=username).first()

def find_user_by_id(user_id):
    """根据ID查找用户"""
    return User.query.get(user_id)

def is_logged_in():
    """检查用户是否已登录"""
    return "user_id" in session

def find_activity(activity_id: int) -> Optional[Activity]:
    """根据ID查找活动"""
    return Activity.query.get(activity_id)

def get_next_activity_id():
    """获取下一个活动ID"""
    max_id = db.session.query(db.func.max(Activity.id)).scalar()
    return max_id + 1 if max_id else 1

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def similar_ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a or '', b or '').ratio()

def find_similar_posts(title: str, content: str, threshold: float = 0.75):
    combined = (title or '') + '\n' + (content or '')
    candidates = []
    for p in Post.query.all():
        score = similar_ratio(combined, (p.title or '') + '\n' + (p.content or ''))
        if score >= threshold:
            candidates.append({'post': {
                'id': p.id,
                'title': p.title,
                'category': p.category,
                'created_at': p.created_at
            }, 'score': score})
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates

def is_teacher(user_id):
    """检查是否为教师"""
    user = find_user_by_id(user_id)
    return user and user.role == 'teacher'

# 登录检查装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# 创建数据库表（启动时自动执行）
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

# ---------------------------- 页面路由 ----------------------------

# 首页
@app.route('/')
@login_required
def home():
    return render_template('index.html')

# 登录页
@app.route('/login')
def login_page():
    # 如果已登录，直接跳转到首页
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template('login.html')

# 注册页
@app.route('/register')
def register_page():
    return render_template('register.html')

# 个人中心页
@app.route('/profile')
@login_required
def profile_page():
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return redirect(url_for('login_page'))
    return render_template("profile.html", user=user)

# 好友管理页
@app.route('/friends')
@login_required
def friends_page():
    return render_template('friends.html')

# 消息中心页
@app.route('/messages')
@login_required
def messages_page():
    return render_template('messages.html')

# 创建活动页
@app.route('/create-activity')
@login_required
def create_activity_page():
    return render_template('create_activity.html')

# 活动详情页
@app.route('/activity/<int:activity_id>')
def activity_detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    initiator = User.query.get(activity.initiator_id) if activity.initiator_id else None
    return render_template('activity_detail.html',
                         activity=activity,
                         initiator=initiator,
                         username=session.get('username'))

# 教师审核页面路由（仅教师可访问）
@app.route('/teacher/review')
@login_required
def teacher_review_page():
    if not is_teacher(session["user_id"]):
        return redirect(url_for('home'))
    return render_template('teacher_review.html')

# ---------------------------- API接口 ----------------------------

# 注册接口（仅允许学生注册）
@app.route('/api/register', methods=['POST'])
def register():
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
        
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ["username", "password", "email"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"success": False, "error": f"缺少字段：{field}"}), 400
        
        # 验证用户名（不能是教师预设用户名）
        if data["username"] in ['teacherA', 'teacherB', 'teacherC', 'teacherD', 'teacherE']:
            return jsonify({"success": False, "error": "该用户名已被系统占用"}), 409
        
        # 验证用户名长度
        if len(data["username"]) < 3 or len(data["username"]) > 20:
            return jsonify({"success": False, "error": "用户名长度需在3-20个字符之间"}), 400
        
        # 检查用户名和邮箱是否已存在
        if find_user(data["username"]):
            return jsonify({"success": False, "error": "用户名已被注册"}), 409
        
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"success": False, "error": "邮箱已存在"}), 409
        
        # 创建新用户（默认身份为学生）
        hashed_password = generate_password_hash(data["password"], method='pbkdf2:sha256')
        
        new_user = User(
            username=data["username"],
            email=data["email"],
            password=hashed_password,
            role='student',  # 固定为学生
            hobbies=data.get("hobbies", ""),
            major=data.get("major", ""),
            grade=data.get("grade", ""),
            real_name=data.get("real_name", ""),
            student_id=data.get("student_id", ""),
            phone=data.get("phone", ""),
            gender=data.get("gender", ""),
            bio=data.get("bio", ""),
            avatar='/static/images/default.jpg'  # 设置默认头像
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "注册成功，请登录",
            "data": {"username": new_user.username, "role": new_user.role}
        }), 201
        
    except Exception as e:
        return jsonify({"success": False, "error": f"服务器错误：{str(e)}"}), 500

# 登录接口
@app.route('/api/login', methods=['POST'])
def login():
    try:
        if not request.is_json:
            return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
        
        data = request.get_json()
        
        if not data or "username" not in data or not data["username"]:
            return jsonify({"success": False, "error": "请输入用户名"}), 400
        
        if "password" not in data or not data["password"]:
            return jsonify({"success": False, "error": "请输入密码"}), 400
        
        # 查找用户并验证密码
        user = find_user(data["username"])
        if not user or not check_password_hash(user.password, data["password"]):
            return jsonify({"success": False, "error": "用户名或密码错误"}), 401
        
        # 记录session
        session.permanent = True
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role  # 记录用户身份
        
        # 注意：Flask 的 SecureCookieSession 没有 sid 属性，这里只打印基础信息即可
        print(f"DEBUG: 用户 {user.username} 登录成功，user_id: {user.id}")
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {"username": user.username, "user_id": user.id, "role": user.role}
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"服务器错误：{str(e)}"}), 500

# 注销接口
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        username = session.get("username", "未知用户")
        session.clear()
        print(f"DEBUG: 用户 {username} 已登出")
        return jsonify({"success": True, "message": "已成功登出"})
    except Exception as e:
        return jsonify({"success": False, "error": f"服务器错误：{str(e)}"}), 500

# 获取当前登录用户信息
@app.route("/api/current-user", methods=["GET"])
def get_current_user():
    if not is_logged_in():
        return jsonify({"success": False, "error": "未登录"}), 401
    
    # 获取用户角色
    user = find_user_by_id(session["user_id"])
    return jsonify({
        "success": True,
        "data": {
            "username": session["username"],
            "user_id": session["user_id"],
            "role": user.role  # 新增角色返回
        }
    })

# 头像上传API
@app.route("/api/user/avatar", methods=["POST"])
@login_required
def upload_avatar():
    """上传用户头像"""
    # 检查是否有文件上传
    if 'avatar' not in request.files:
        return jsonify({"success": False, "error": "没有选择文件"}), 400
    
    file = request.files['avatar']
    
    # 如果用户没有选择文件，浏览器会提交一个空文件
    if file.filename == '':
        return jsonify({"success": False, "error": "没有选择文件"}), 400
    
    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": "不支持的文件类型，仅支持PNG、JPG、JPEG、GIF"}), 400
    
    # 检查文件大小（2MB）
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    file.seek(0)
    if file_length > 2 * 1024 * 1024:
        return jsonify({"success": False, "error": "文件太大，最大支持2MB"}), 400
    
    # 获取当前用户
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 生成安全的文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = secure_filename(file.filename)
    file_extension = original_filename.rsplit('.', 1)[1].lower()
    new_filename = f"{user.id}_{timestamp}.{file_extension}"
    
    # 修正保存路径（与访问路径一致）
    save_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'avatars')
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, new_filename)
    
    try:
        # 保存文件
        file.save(file_path)
        
        # 更新数据库中的头像路径（相对路径）
        avatar_url = f"/static/uploads/avatars/{new_filename}"
        user.avatar = avatar_url
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "头像上传成功",
            "data": {
                "avatar_url": avatar_url,
                "filename": new_filename
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"上传失败：{str(e)}"}), 500

@app.route("/api/user/avatar-info", methods=["GET"])
@login_required
def get_avatar_info():
    """获取用户当前头像信息"""
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    return jsonify({
        "success": True,
        "data": {
            "avatar_url": user.avatar,
            "has_custom_avatar": user.avatar != "/static/images/default.jpg"
        }
    })

# ---------------------------- 活动API ----------------------------

# 获取所有活动接口
@app.route('/api/activities', methods=['GET'])
def get_activities():
    activities = Activity.query.order_by(Activity.id.desc()).all()
    result = []
    for act in activities:
        result.append({
            "id": act.id,
            "title": act.title,
            "type": act.type,
            "time": act.time,
            "location": act.location,
            "tags": act.tags,
            "description": act.description,
            "initiator_id": act.initiator_id,
            "participants": [{"id": p.id, "name": p.username} for p in act.participants],
            "participant_count": len(act.participants),
            "created_at": act.created_at
        })
    return jsonify({"success": True, "data": result, "count": len(result)}), 200

# 获取单个活动详情
@app.route("/api/activities/<int:activity_id>", methods=["GET"])
def get_activity(activity_id: int):
    activity = find_activity(activity_id)
    if activity:
        return jsonify({
            "success": True,
            "data": {
                "id": activity.id,
                "title": activity.title,
                "type": activity.type,
                "time": activity.time,
                "location": activity.location,
                "tags": activity.tags,
                "description": activity.description,
                "initiator_id": activity.initiator_id,
                "participants": [{"id": p.id, "name": p.username} for p in activity.participants],
                "participant_count": len(activity.participants),
                "created_at": activity.created_at
            }
        })
    return jsonify({"success": False, "error": "活动不存在"}), 404

# 创建活动接口（教师和学生均可创建）
@app.route('/api/activities', methods=['POST'])
@login_required
def create_activity():
    if not request.json:
        return jsonify({"success": False, "error": "请求数据为空或格式不正确"}), 400
    
    data = request.get_json()
    required_fields = ["title", "type", "time", "location"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"success": False, "error": f"缺少必要字段: {field}"}), 400
    
    # 生成新活动
    new_activity = Activity(
        title=data["title"],
        type=data["type"],
        time=data["time"],
        location=data["location"],
        tags=data.get("tags", ""),
        description=data.get("description", ""),
        initiator_id=session["user_id"]
    )
    
    db.session.add(new_activity)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "活动创建成功",
        "data": {
            "id": new_activity.id,
            "title": new_activity.title,
            "type": new_activity.type,
            "time": new_activity.time,
            "location": new_activity.location
        }
    }), 201

# 活动删除接口（仅教师可删除）
@app.route('/api/activities/<int:activity_id>', methods=['DELETE'])
@login_required
def delete_activity(activity_id):
    if not is_teacher(session["user_id"]):
        return jsonify({"success": False, "error": "仅教师可删除活动"}), 403
    
    activity = find_activity(activity_id)
    if not activity:
        return jsonify({"success": False, "error": "活动不存在"}), 404
    
    try:
        db.session.delete(activity)
        db.session.commit()
        return jsonify({"success": True, "message": "活动已删除"})
    except Exception as e:
        return jsonify({"success": False, "error": f"删除失败：{str(e)}"}), 500

# 活动报名接口
@app.route('/api/activities/<int:activity_id>/join', methods=['POST'])
@login_required
def join_activity(activity_id: int):
    activity = find_activity(activity_id)
    if not activity:
        return jsonify({"success": False, "error": "活动不存在"}), 404
    
    user = find_user_by_id(session["user_id"])
    
    # 检查是否已报名
    if user in activity.participants:
        return jsonify({"success": False, "error": "您已报名该活动"}), 400
    
    activity.participants.append(user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"成功报名活动: {activity.title}",
        "data": {
            "activity_id": activity_id,
            "participants_count": len(activity.participants)
        }
    })

# 取消报名接口
@app.route("/api/activities/<int:activity_id>/leave", methods=["POST"])
@login_required
def leave_activity(activity_id: int):
    activity = find_activity(activity_id)
    if not activity:
        return jsonify({"success": False, "error": "活动不存在"}), 404
    
    user = find_user_by_id(session["user_id"])
    if user not in activity.participants:
        return jsonify({"success": False, "error": "您未报名该活动"}), 400
    
    activity.participants.remove(user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"已取消报名活动: {activity.title}",
        "data": {
            "activity_id": activity_id,
            "participants_count": len(activity.participants)
        }
    })

# 活动收藏/取消收藏接口
@app.route("/api/activities/<int:activity_id>/favorite", methods=["POST"])
@login_required
def favorite_activity(activity_id: int):
    activity = find_activity(activity_id)
    if not activity:
        return jsonify({"success": False, "error": "活动不存在"}), 404
    
    user = find_user_by_id(session["user_id"])
    is_favorited = activity in user.favorite_activities
    
    if is_favorited:
        # 取消收藏
        user.favorite_activities.remove(activity)
        message = "已取消收藏"
    else:
        # 添加收藏
        user.favorite_activities.append(activity)
        message = "活动已收藏"
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": message,
        "data": {
            "activity_id": activity_id,
            "is_favorited": not is_favorited,
            "favorites_count": len(user.favorite_activities)
        }
    })

# 活动搜索接口
@app.route("/api/activities/search", methods=["GET"])
@login_required
def search_activities():
    keyword = request.args.get('keyword', '').strip()
    search_type = request.args.get('type', 'all')
    
    # 构建查询条件
    query = Activity.query
    if search_type != 'all':
        query = query.filter(Activity.type == search_type)
    
    if keyword:
        keyword = f"%{keyword}%"
        query = query.filter(
            db.or_(Activity.title.like(keyword), Activity.location.like(keyword))
        )
    
    activities = query.order_by(Activity.id.desc()).all()
    result = []
    
    for act in activities:
        result.append({
            "id": act.id,
            "title": act.title,
            "type": act.type,
            "time": act.time,
            "location": act.location,
            "participants_count": len(act.participants)
        })
    
    return jsonify({
        "success": True,
        "data": result,
        "count": len(result),
        "search_info": {"keyword": keyword.strip('%') if keyword else '', "type": search_type}
    })

# 活动推荐接口
@app.route('/api/activities/recommend', methods=['GET'])
@login_required
def recommend_activities():
    # 获取当前用户的兴趣标签
    user = find_user_by_id(session['user_id'])
    user_hobbies = user.hobbies.split(',') if user.hobbies else []
    
    if not user_hobbies:
        return jsonify({'success': True, 'activities': [], 'message': '暂无兴趣标签，推荐热门活动'}), 200
    
    # 匹配活动标签（包含任意一个兴趣标签）
    recommended = []
    activities = Activity.query.order_by(Activity.id.desc()).all()
    
    for act in activities:
        act_tags = act.tags.split(',') if act.tags else []
        if any(tag in user_hobbies for tag in act_tags):
            recommended.append({
                'id': act.id,
                'title': act.title,
                'type': act.type,
                'time': act.time,
                'location': act.location,
                'tags': act.tags,
                'participant_count': len(act.participants)
            })
    
    return jsonify({'success': True, 'activities': recommended}), 200

# ---------------------------- 帖子与结构化发布 API ----------------------------

@app.route('/api/post-templates', methods=['GET'])
def get_post_templates():
    return jsonify({'success': True, 'data': POST_TEMPLATES, 'categories': POST_CATEGORIES})

@app.route('/api/posts/similar', methods=['GET'])
def api_similar_posts():
    title = request.args.get('title', '')
    content = request.args.get('content', '')
    
    try:
        threshold = float(request.args.get('threshold', 0.75))
    except Exception:
        threshold = 0.75
    
    candidates = find_similar_posts(title, content, threshold)
    return jsonify({'success': True, 'data': candidates, 'count': len(candidates)})

# 获取帖子列表（仅显示审核通过或自己发布的帖子）
@app.route('/api/posts', methods=['GET'])
def list_posts_api():
    category = request.args.get('category')
    tag = request.args.get('tag')
    query = Post.query.order_by(Post.id.desc())
    
    if category:
        query = query.filter(Post.category == category)
    
    # 过滤条件：审核通过 或 自己发布的帖子
    current_user_id = session.get('user_id')
    if current_user_id:
        query = query.filter(
            db.or_(
                Post.review_status == 'approved',
                Post.author_id == current_user_id
            )
        )
    else:
        query = query.filter(Post.review_status == 'approved')
    
    results = []
    for p in query.all():
        tags = p.tags.split(',') if p.tags else []
        if tag and tag not in tags:
            continue
        
        media = []
        try:
            media = json.loads(p.media) if p.media else []
        except Exception:
            media = []
        
        metadata = {}
        try:
            metadata = json.loads(p.metadata_json) if p.metadata_json else {}
        except Exception:
            metadata = {}
        
        results.append({
            'id': p.id,
            'title': p.title,
            'category': p.category,
            'content': p.content,
            'is_markdown': p.is_markdown,
            'tags': tags,
            'media': media,
            'metadata': metadata,
            'author_id': p.author_id,
            'is_official': p.is_official,
            'org_name': p.org_name,
            'review_status': p.review_status,
            'created_at': p.created_at
        })
    
    return jsonify({'success': True, 'data': results, 'count': len(results)})

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post_api(post_id: int):
    p = Post.query.get(post_id)
    if not p:
        return jsonify({'success': False, 'error': '帖子不存在'}), 404
    
    # 权限验证：审核通过 或 自己发布的帖子
    current_user_id = session.get('user_id')
    if p.review_status != 'approved' and p.author_id != current_user_id and not is_teacher(current_user_id):
        return jsonify({'success': False, 'error': '该帖子未审核或无访问权限'}), 403
    
    try:
        media = json.loads(p.media) if p.media else []
    except Exception:
        media = []
    
    try:
        metadata = json.loads(p.metadata_json) if p.metadata_json else {}
    except Exception:
        metadata = {}
    
    return jsonify({'success': True, 'data': {
        'id': p.id,
        'title': p.title,
        'category': p.category,
        'content': p.content,
        'is_markdown': p.is_markdown,
        'tags': p.tags.split(',') if p.tags else [],
        'media': media,
        'metadata': metadata,
        'author_id': p.author_id,
        'is_official': p.is_official,
        'org_name': p.org_name,
        'review_status': p.review_status,
        'created_at': p.created_at
    }})

# 创建帖子接口（学生发布需审核，教师发布直接通过）
@app.route('/api/posts', methods=['POST'])
@login_required
def create_post_api():
    # 支持 JSON 或 multipart/form-data
    title = None
    category = None
    content = ''
    is_markdown = False
    tags = []
    metadata = {}
    uploaded_media = []
    
    if request.is_json:
        data = request.get_json()
        title = data.get('title')
        category = data.get('category')
        content = data.get('content', '')
        is_markdown = bool(data.get('is_markdown', False))
        tags = data.get('tags', [])
        metadata = data.get('metadata', {})
        force = bool(data.get('force', False))
    else:
        title = request.form.get('title')
        category = request.form.get('category')
        content = request.form.get('content', '')
        is_markdown = request.form.get('is_markdown', 'false').lower() == 'true'
        tags = [t.strip() for t in (request.form.get('tags', '') or '').split(',') if t.strip()]
        force = request.form.get('force', 'false').lower() == 'true'
        
        # metadata字段可以通过JSON字符串传入
        try:
            metadata = json.loads(request.form.get('metadata', '{}'))
        except Exception:
            metadata = {}
        
        # 文件
        if 'files' in request.files:
            files = request.files.getlist('files')
            for f in files:
                if f and allowed_file(f.filename):
                    fname = secure_filename(f.filename)
                    unique = f"{uuid.uuid4().hex[:8]}_{fname}"
                    save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique)
                    f.save(save_path)
                    normalized_path = save_path.replace('\\', '/')
                    uploaded_media.append({'url': f"/{normalized_path}", 'filename': fname})
    
    if not title or not category:
        return jsonify({'success': False, 'error': '缺少 title 或 category'}), 400
    
    if category not in POST_CATEGORIES:
        return jsonify({'success': False, 'error': '无效的分类'}), 400
    
    # 检测相似度
    duplicates = find_similar_posts(title, content)
    if duplicates and not force:
        return jsonify({'success': False, 'error': '可能存在相似信息，建议合并或查看原帖', 'possible_duplicates': duplicates}), 409
    
    # 确定审核状态：教师直接通过，学生需审核
    review_status = 'approved' if is_teacher(session.get('user_id')) else 'pending'
    
    # 创建帖子
    p = Post(
        title=title,
        category=category,
        content=content,
        is_markdown=is_markdown,
        tags=','.join(tags),
        media=json.dumps(uploaded_media, ensure_ascii=False),
        metadata_json=json.dumps(metadata, ensure_ascii=False),
        author_id=session.get('user_id'),
        is_official=False,
        org_name='',
        review_status=review_status
    )
    
    db.session.add(p)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'发布成功{",等待教师审核" if review_status == "pending" else ""}',
        'data': {'id': p.id, 'review_status': review_status}
    }), 201

# 帖子删除接口（自己的帖子或教师可删除）
@app.route('/api/posts/<int:post_id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'success': False, 'error': '帖子不存在'}), 404
    
    # 权限判断：自己的帖子或教师
    if post.author_id != session["user_id"] and not is_teacher(session["user_id"]):
        return jsonify({'success': False, 'error': '无权限删除该帖子'}), 403
    
    try:
        db.session.delete(post)
        db.session.commit()
        return jsonify({"success": True, "message": "帖子已删除"})
    except Exception as e:
        return jsonify({"success": False, "error": f"删除失败：{str(e)}"}), 500

# 帖子审核接口（仅教师可操作）
@app.route('/api/posts/<int:post_id>/review', methods=['POST'])
@login_required
def review_post(post_id):
    if not is_teacher(session["user_id"]):
        return jsonify({"success": False, "error": "仅教师可审核帖子"}), 403
    
    post = Post.query.get(post_id)
    if not post:
        return jsonify({"success": False, "error": "帖子不存在"}), 404
    
    data = request.get_json()
    if "status" not in data or data["status"] not in ['approved', 'rejected']:
        return jsonify({"success": False, "error": "状态必须是approved或rejected"}), 400
    
    # 记录审核结果
    review = PostReview(
        post_id=post_id,
        teacher_id=session["user_id"],
        status=data["status"],
        comment=data.get("comment", "")
    )
    
    # 更新帖子审核状态
    post.review_status = data["status"]
    
    try:
        db.session.add(review)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"帖子已{data['status']}",
            "data": {"review_id": review.id, "post_status": post.review_status}
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"审核失败：{str(e)}"}), 500

# 获取待审核帖子列表（仅教师）
@app.route('/api/posts/pending', methods=['GET'])
@login_required
def get_pending_posts():
    if not is_teacher(session["user_id"]):
        return jsonify({"success": False, "error": "仅教师可查看待审核帖子"}), 403
    
    posts = Post.query.filter_by(review_status='pending').order_by(Post.id.desc()).all()
    result = []
    
    for p in posts:
        author = find_user_by_id(p.author_id)
        result.append({
            "id": p.id,
            "title": p.title,
            "content": p.content[:100] + "..." if len(p.content) > 100 else p.content,
            "category": p.category,
            "author": author.username if author else "未知用户",
            "created_at": p.created_at
        })
    
    return jsonify({"success": True, "data": result, "count": len(result)})

# 帖子互动：点赞/收藏/转发/有用/打赏等
@app.route('/api/posts/<int:post_id>/react', methods=['POST'])
@login_required
def post_react(post_id: int):
    p = Post.query.get(post_id)
    if not p:
        return jsonify({'success': False, 'error': '帖子不存在'}), 404
    
    data = request.get_json() or {}
    rtype = data.get('type')
    if not rtype:
        return jsonify({'success': False, 'error': '缺少 type 字段'}), 400
    
    # 记录反应
    try:
        react = Reaction(
            user_id=session.get('user_id'),
            post_id=post_id,
            type=rtype,
            metadata_json=json.dumps(data.get('metadata', {}), ensure_ascii=False)
        )
        db.session.add(react)
        db.session.commit()
        return jsonify({'success': True, 'message': '已记录互动'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'服务器错误：{str(e)}'}), 500

# 获取帖子评论（含嵌套）
@app.route('/api/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id: int):
    p = Post.query.get(post_id)
    if not p:
        return jsonify({'success': False, 'error': '帖子不存在'}), 404
    
    # 权限验证：审核通过 或 自己发布的帖子 或 教师
    current_user_id = session.get('user_id')
    if p.review_status != 'approved' and p.author_id != current_user_id and not is_teacher(current_user_id):
        return jsonify({'success': False, 'error': '该帖子未审核或无访问权限'}), 403
    
    # 获取所有评论并构建树形
    all_comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.asc()).all()
    
    comments_by_id = {c.id: {
        'id': c.id,
        'post_id': c.post_id,
        'author_id': c.author_id,
        'content': c.content,
        'parent_id': c.parent_id,
        'is_pinned': c.is_pinned,
        'created_at': c.created_at,
        'children': []
    } for c in all_comments}
    
    roots = []
    for c in comments_by_id.values():
        if c['parent_id'] and c['parent_id'] in comments_by_id:
            comments_by_id[c['parent_id']]['children'].append(c)
        else:
            roots.append(c)
    
    return jsonify({'success': True, 'data': roots, 'count': len(all_comments)}), 200

# 提交评论或回复
@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def post_comment(post_id: int):
    p = Post.query.get(post_id)
    if not p:
        return jsonify({'success': False, 'error': '帖子不存在'}), 404
    
    # 权限验证：审核通过 或 自己发布的帖子 或 教师
    current_user_id = session.get('user_id')
    if p.review_status != 'approved' and p.author_id != current_user_id and not is_teacher(current_user_id):
        return jsonify({'success': False, 'error': '该帖子未审核或无评论权限'}), 403
    
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    parent_id = data.get('parent_id')
    
    if not content:
        return jsonify({'success': False, 'error': '评论内容不能为空'}), 400
    
    # 如果 parent_id 提供，检查父评论是否存在
    if parent_id:
        parent = Comment.query.get(parent_id)
        if not parent or parent.post_id != post_id:
            return jsonify({'success': False, 'error': '父评论不存在'}), 400
    
    try:
        c = Comment(post_id=post_id, author_id=session.get('user_id'), content=content, parent_id=parent_id)
        db.session.add(c)
        db.session.commit()
        return jsonify({'success': True, 'message': '评论已发布', 'data': {'id': c.id}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'服务器错误：{str(e)}'}), 500

# ---------------------------- 小组API ----------------------------

@app.route('/api/groups', methods=['GET', 'POST'])
def api_groups():
    if request.method == 'GET':
        gs = Group.query.order_by(Group.id.desc()).all()
        return jsonify({'success': True, 'data': [{'id': g.id, 'name': g.name, 'description': g.description} for g in gs]})
    
    # 创建小组
    if not is_logged_in():
        return jsonify({'success': False, 'error': '请先登录'}), 401
    
    data = request.get_json() or {}
    name = data.get('name')
    desc = data.get('description', '')
    
    if not name:
        return jsonify({'success': False, 'error': '需要提供小组名称'}), 400
    
    if Group.query.filter_by(name=name).first():
        return jsonify({'success': False, 'error': '小组名称已存在'}), 409
    
    g = Group(name=name, description=desc, creator_id=session.get('user_id'))
    db.session.add(g)
    db.session.commit()
    
    return jsonify({'success': True, 'message': '小组创建成功', 'data': {'id': g.id, 'name': g.name}}), 201

# ---------------------------- 个人中心API ----------------------------

# 获取用户基本资料
@app.route("/api/user/profile", methods=["GET"])
@login_required
def get_user_profile():
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 计算统计数据
    participated_count = len(user.joined_activities)
    favorites_count = len(user.favorite_activities)
    total_activities = Activity.query.count()
    
    return jsonify({
        "success": True,
        "data": {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "stats": {
                "activities_joined": participated_count,
                "total_activities": total_activities,
                "favorites_count": favorites_count
            },
            "avatar": user.avatar,
            "user_id": user.id  # 新增返回用户ID
        }
    })

# 更新用户基本资料（邮箱）
@app.route("/api/user/profile", methods=["PUT"])
@login_required
def update_user_profile():
    if not request.is_json:
        return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
    
    data = request.get_json()
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 更新邮箱
    if "email" in data and data["email"]:
        if "@" not in data["email"] or "." not in data["email"]:
            return jsonify({"success": False, "error": "邮箱格式不正确"}), 400
        
        # 检查邮箱是否已被其他用户使用
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user and existing_user.id != user_id:
            return jsonify({"success": False, "error": "该邮箱已被其他用户使用"}), 409
        
        user.email = data["email"]
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "个人资料更新成功",
        "data": {"username": user.username, "email": user.email}
    })

# 获取用户详细资料
@app.route("/api/user/profile/detailed", methods=["GET"])
@login_required
def get_detailed_profile():
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 返回所有个人资料字段
    profile_data = {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "real_name": user.real_name,
        "student_id": user.student_id,
        "major": user.major,
        "grade": user.grade,
        "phone": user.phone,
        "gender": user.gender,
        "bio": user.bio,
        "avatar": user.avatar,
        "created_at": user.created_at,
        "user_id": user.id
    }
    
    return jsonify({"success": True, "data": profile_data})

# 更新用户详细资料
@app.route("/api/user/profile/detailed", methods=["PUT"])
@login_required
def update_detailed_profile():
    if not request.is_json:
        return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
    
    data = request.get_json()
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 允许更新的字段列表
    updatable_fields = ["real_name", "student_id", "major", "grade", "phone", "gender", "bio", "email"]
    updated_fields = []
    
    for field in updatable_fields:
        if field in data:
            # 验证手机号
            if field == "phone" and data[field]:
                phone = data[field]
                if not phone.isdigit() or len(phone) != 11:
                    return jsonify({"success": False, "error": "手机号格式不正确，应为11位数字"}), 400
            
            # 验证邮箱
            if field == "email" and data[field]:
                email = data[field]
                if "@" not in email or "." not in email:
                    return jsonify({"success": False, "error": "邮箱格式不正确"}), 400
                
                # 检查邮箱是否已被其他用户使用
                existing_user = User.query.filter_by(email=email).first()
                if existing_user and existing_user.id != user_id:
                    return jsonify({"success": False, "error": "该邮箱已被其他用户使用"}), 409
            
            # 更新字段
            setattr(user, field, data[field])
            updated_fields.append(field)
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"成功更新{len(updated_fields)}个字段",
        "data": {"username": user.username, "updated_fields": updated_fields}
    })

# 获取用户参与的活动
@app.route("/api/user/joined-activities", methods=["GET"])
@login_required
def get_joined_activities():
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 格式化活动数据
    joined_activities = []
    for activity in user.joined_activities:
        joined_activities.append({
            "id": activity.id,
            "title": activity.title,
            "type": activity.type,
            "time": activity.time,
            "location": activity.location,
            "participants": [{"id": p.id, "name": p.username} for p in activity.participants],
            "created_at": activity.created_at
        })
    
    return jsonify({"success": True, "data": joined_activities, "count": len(joined_activities)})

# 获取用户收藏的活动
@app.route("/api/user/favorites", methods=["GET"])
@login_required
def get_user_favorites_api():
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 格式化收藏活动数据
    favorite_activities = []
    for activity in user.favorite_activities:
        favorite_activities.append({
            "id": activity.id,
            "title": activity.title,
            "type": activity.type,
            "time": activity.time,
            "location": activity.location,
            "participants": [{"id": p.id, "name": p.username} for p in activity.participants],
            "created_at": activity.created_at
        })
    
    return jsonify({"success": True, "data": favorite_activities, "count": len(favorite_activities)})

# 修改密码接口
@app.route('/api/user/change-password', methods=['POST'])
@login_required
def change_password():
    if not request.is_json:
        return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
    
    data = request.get_json()
    
    # 验证参数
    if not data.get('current_password') or not data.get('new_password'):
        return jsonify({"success": False, "error": "请提供当前密码和新密码"}), 400
    
    # 验证新密码长度
    if len(data.get('new_password')) < 8:
        return jsonify({"success": False, "error": "新密码长度至少8位"}), 400
    
    # 获取当前用户
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 验证当前密码
    if not check_password_hash(user.password, data.get('current_password')):
        return jsonify({"success": False, "error": "当前密码不正确"}), 401
    
    # 更新密码
    user.password = generate_password_hash(data.get('new_password'), method='pbkdf2:sha256')
    db.session.commit()
    
    return jsonify({"success": True, "message": "密码修改成功，请重新登录"})

# ---------------------------- 好友功能API ----------------------------

# 发送好友请求
@app.route('/api/friends/request', methods=['POST'])
@login_required
def send_friend_request():
    if not request.is_json:
        return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
    
    data = request.get_json()
    target_user_id = data.get('user_id')
    
    if not target_user_id:
        return jsonify({"success": False, "error": "请提供目标用户ID"}), 400
    
    current_user_id = session["user_id"]
    
    # 不能添加自己为好友
    if current_user_id == target_user_id:
        return jsonify({"success": False, "error": "不能添加自己为好友"}), 400
    
    # 检查目标用户是否存在
    target_user = find_user_by_id(target_user_id)
    if not target_user:
        return jsonify({"success": False, "error": "目标用户不存在"}), 404
    
    # 检查是否已经是好友或已有请求
    # 确保 user1_id < user2_id 以保持一致性
    user1_id = min(current_user_id, target_user_id)
    user2_id = max(current_user_id, target_user_id)
    
    existing_friendship = Friendship.query.filter_by(
        user1_id=user1_id,
        user2_id=user2_id
    ).first()
    
    if existing_friendship:
        if existing_friendship.status == 'accepted':
            return jsonify({"success": False, "error": "你们已经是好友了"}), 400
        elif existing_friendship.status == 'pending':
            return jsonify({"success": False, "error": "好友请求已发送，等待对方处理"}), 400
    
    # 创建好友请求
    friendship = Friendship(
        user1_id=user1_id,
        user2_id=user2_id,
        status='pending',
        requester_id=current_user_id
    )
    
    try:
        db.session.add(friendship)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "好友请求已发送",
            "data": {"friendship_id": friendship.id}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"发送失败：{str(e)}"}), 500

# 处理好友请求（接受/拒绝）
@app.route('/api/friends/request/<int:friendship_id>', methods=['POST'])
@login_required
def handle_friend_request(friendship_id):
    if not request.is_json:
        return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
    
    data = request.get_json()
    action = data.get('action')  # 'accept' 或 'reject'
    
    if action not in ['accept', 'reject']:
        return jsonify({"success": False, "error": "action必须是accept或reject"}), 400
    
    current_user_id = session["user_id"]
    friendship = Friendship.query.get(friendship_id)
    
    if not friendship:
        return jsonify({"success": False, "error": "好友请求不存在"}), 404
    
    # 检查是否有权限处理（必须是接收方）
    if friendship.user1_id != current_user_id and friendship.user2_id != current_user_id:
        return jsonify({"success": False, "error": "无权限处理此请求"}), 403
    
    # 检查是否是请求发起者
    if friendship.requester_id == current_user_id:
        return jsonify({"success": False, "error": "不能处理自己发起的请求"}), 400
    
    # 检查请求状态
    if friendship.status != 'pending':
        return jsonify({"success": False, "error": "该请求已处理"}), 400
    
    # 更新状态
    friendship.status = 'accepted' if action == 'accept' else 'rejected'
    friendship.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"已{'接受' if action == 'accept' else '拒绝'}好友请求",
            "data": {"status": friendship.status}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"处理失败：{str(e)}"}), 500

# 获取好友列表
@app.route('/api/friends', methods=['GET'])
@login_required
def get_friends():
    current_user_id = session["user_id"]
    
    # 获取所有已接受的好友关系
    friendships = Friendship.query.filter(
        db.or_(
            Friendship.user1_id == current_user_id,
            Friendship.user2_id == current_user_id
        ),
        Friendship.status == 'accepted'
    ).all()
    
    friends = []
    for friendship in friendships:
        # 确定对方用户ID
        friend_id = friendship.user2_id if friendship.user1_id == current_user_id else friendship.user1_id
        friend_user = find_user_by_id(friend_id)
        
        if friend_user:
            friends.append({
                "user_id": friend_user.id,
                "username": friend_user.username,
                "avatar": friend_user.avatar,
                "bio": friend_user.bio,
                "created_at": friendship.created_at
            })
    
    return jsonify({
        "success": True,
        "data": friends,
        "count": len(friends)
    })

# 获取待处理的好友请求（收到的请求）
@app.route('/api/friends/requests', methods=['GET'])
@login_required
def get_friend_requests():
    current_user_id = session["user_id"]
    
    # 获取所有待处理的请求（对方发起的）
    requests = Friendship.query.filter(
        db.or_(
            Friendship.user1_id == current_user_id,
            Friendship.user2_id == current_user_id
        ),
        Friendship.status == 'pending',
        Friendship.requester_id != current_user_id
    ).all()
    
    result = []
    for req in requests:
        requester_id = req.requester_id
        requester = find_user_by_id(requester_id)
        
        if requester:
            result.append({
                "friendship_id": req.id,
                "requester_id": requester.id,
                "requester_username": requester.username,
                "requester_avatar": requester.avatar,
                "created_at": req.created_at
            })
    
    return jsonify({
        "success": True,
        "data": result,
        "count": len(result)
    })

# 删除好友
@app.route('/api/friends/<string:friend_id>', methods=['DELETE'])
@login_required
def delete_friend(friend_id):
    current_user_id = session["user_id"]
    
    # 确保 user1_id < user2_id
    user1_id = min(current_user_id, friend_id)
    user2_id = max(current_user_id, friend_id)
    
    friendship = Friendship.query.filter_by(
        user1_id=user1_id,
        user2_id=user2_id,
        status='accepted'
    ).first()
    
    if not friendship:
        return jsonify({"success": False, "error": "好友关系不存在"}), 404
    
    try:
        db.session.delete(friendship)
        db.session.commit()
        return jsonify({"success": True, "message": "已删除好友"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"删除失败：{str(e)}"}), 500

# ---------------------------- 消息功能API ----------------------------

# 发送消息
@app.route('/api/messages', methods=['POST'])
@login_required
def send_message():
    if not request.is_json:
        return jsonify({"success": False, "error": "请求格式必须为JSON"}), 400
    
    data = request.get_json()
    receiver_id = data.get('receiver_id')
    content = data.get('content', '').strip()
    
    if not receiver_id:
        return jsonify({"success": False, "error": "请提供接收者ID"}), 400
    
    if not content:
        return jsonify({"success": False, "error": "消息内容不能为空"}), 400
    
    current_user_id = session["user_id"]
    
    # 不能给自己发消息
    if current_user_id == receiver_id:
        return jsonify({"success": False, "error": "不能给自己发消息"}), 400
    
    # 检查接收者是否存在
    receiver = find_user_by_id(receiver_id)
    if not receiver:
        return jsonify({"success": False, "error": "接收者不存在"}), 404
    
    # 检查是否是好友关系（可选：如果要求必须是好友才能发消息）
    user1_id = min(current_user_id, receiver_id)
    user2_id = max(current_user_id, receiver_id)
    friendship = Friendship.query.filter_by(
        user1_id=user1_id,
        user2_id=user2_id,
        status='accepted'
    ).first()
    
    # 注释掉这个检查，允许非好友也能发消息
    # if not friendship:
    #     return jsonify({"success": False, "error": "只能给好友发消息"}), 403
    
    # 创建消息
    message = Message(
        sender_id=current_user_id,
        receiver_id=receiver_id,
        content=content,
        is_read=False
    )
    
    try:
        db.session.add(message)
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "消息已发送",
            "data": {
                "message_id": message.id,
                "created_at": message.created_at
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"发送失败：{str(e)}"}), 500

# 获取与某个用户的聊天记录
@app.route('/api/messages/<string:user_id>', methods=['GET'])
@login_required
def get_messages(user_id):
    current_user_id = session["user_id"]
    
    # 检查目标用户是否存在
    target_user = find_user_by_id(user_id)
    if not target_user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 获取双方的所有消息（按时间排序）
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user_id, Message.receiver_id == user_id),
            db.and_(Message.sender_id == user_id, Message.receiver_id == current_user_id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # 标记未读消息为已读
    unread_messages = [m for m in messages if m.receiver_id == current_user_id and not m.is_read]
    for msg in unread_messages:
        msg.is_read = True
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    
    # 格式化消息数据
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "receiver_id": msg.receiver_id,
            "content": msg.content,
            "is_read": msg.is_read,
            "created_at": msg.created_at,
            "is_own": msg.sender_id == current_user_id
        })
    
    return jsonify({
        "success": True,
        "data": result,
        "count": len(result),
        "target_user": {
            "user_id": target_user.id,
            "username": target_user.username,
            "avatar": target_user.avatar
        }
    })

# 获取所有聊天会话列表（最近联系的人）
@app.route('/api/messages/conversations', methods=['GET'])
@login_required
def get_conversations():
    current_user_id = session["user_id"]
    
    # 获取所有有消息往来的用户
    # 获取所有与当前用户相关的消息
    all_messages = Message.query.filter(
        db.or_(
            Message.sender_id == current_user_id,
            Message.receiver_id == current_user_id
        )
    ).order_by(Message.created_at.desc()).all()
    
    conversations = []
    seen_users = set()
    
    for msg in all_messages:
        # 确定对方用户ID
        other_user_id = msg.receiver_id if msg.sender_id == current_user_id else msg.sender_id
        
        if other_user_id not in seen_users:
            seen_users.add(other_user_id)
            other_user = find_user_by_id(other_user_id)
            
            if other_user:
                # 获取未读消息数
                unread_count = Message.query.filter_by(
                    sender_id=other_user_id,
                    receiver_id=current_user_id,
                    is_read=False
                ).count()
                
                # 获取最后一条消息（当前消息就是按时间倒序的，第一个就是最新的）
                conversations.append({
                    "user_id": other_user.id,
                    "username": other_user.username,
                    "avatar": other_user.avatar,
                    "last_message": msg.content,
                    "last_message_time": msg.created_at,
                    "unread_count": unread_count,
                    "is_own_last_message": msg.sender_id == current_user_id
                })
    
    return jsonify({
        "success": True,
        "data": conversations,
        "count": len(conversations)
    })

# 获取未读消息数
@app.route('/api/messages/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    current_user_id = session["user_id"]
    
    unread_count = Message.query.filter_by(
        receiver_id=current_user_id,
        is_read=False
    ).count()
    
    return jsonify({
        "success": True,
        "data": {"unread_count": unread_count}
    })

# 搜索用户（用于添加好友）
@app.route('/api/users/search', methods=['GET'])
@login_required
def search_users():
    keyword = request.args.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({"success": False, "error": "请提供搜索关键词"}), 400
    
    current_user_id = session["user_id"]
    
    # 搜索用户名或邮箱
    users = User.query.filter(
        db.or_(
            User.username.like(f"%{keyword}%"),
            User.email.like(f"%{keyword}%")
        ),
        User.id != current_user_id
    ).limit(20).all()
    
    result = []
    for user in users:
        # 检查好友关系状态
        user1_id = min(current_user_id, user.id)
        user2_id = max(current_user_id, user.id)
        friendship = Friendship.query.filter_by(
            user1_id=user1_id,
            user2_id=user2_id
        ).first()
        
        friendship_status = None
        if friendship:
            friendship_status = friendship.status
        
        result.append({
            "user_id": user.id,
            "username": user.username,
            "avatar": user.avatar,
            "bio": user.bio,
            "friendship_status": friendship_status  # None, 'pending', 'accepted', 'rejected'
        })
    
    return jsonify({
        "success": True,
        "data": result,
        "count": len(result)
    })

@app.route('/personal_home')
@login_required
def personal_home():
    """个性化首页，适配项目Activity模型的实际字段"""
    
    # 获取当前登录用户信息
    current_user_id = session['user_id']
    current_user = User.query.get(current_user_id)
    if not current_user:
        return redirect(url_for('login_page'))
    
    # 模块1：获取用户待参与活动（未开始=upcoming、按活动时间升序排序）
    upcoming_activities = Activity.query.filter(
        Activity.status == "upcoming",  # 适配你项目的status字段值
    ).order_by(Activity.time.asc()).limit(5).all()  # 取前5条，按时间升序
    
    # 模块2：获取校园热门活动（按参与人数降序排序，适配participant_count字段）
    hot_activities = Activity.query.filter(
        Activity.status == "upcoming"
    ).order_by(Activity.participant_count.desc()).limit(6).all()  # 适配新增的participant_count字段
    
    # 模块3：获取最新校园帖子（按创建时间降序排序，保持原有逻辑）
    latest_posts = Post.query.order_by(Post.created_at.desc()).limit(4).all()  # 若你Post表创建时间字段是其他名称，可留言调整
    
    # 传递数据到前端页面
    return render_template(
        'personal_home.html',
        current_user=current_user,
        upcoming_activities=upcoming_activities,
        hot_activities=hot_activities,
        latest_posts=latest_posts
    )

# ---------------------------- 运行应用 ----------------------------

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)