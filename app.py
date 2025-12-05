from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)
CORS(app, supports_credentials=True)  # 支持跨域请求携带cookie
app.secret_key = 'campus_social_2025'  # 用于session加密
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7  # Session有效期7天
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
    f"{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}?charset=utf8mb4"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------------- 数据库模型（整合后） --------------------------
class User(db.Model):
    id = db.Column(db.String(8), primary_key=True, default=lambda: str(uuid.uuid4())[:8])  # 兼容文件二的UUID格式
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    hobbies = db.Column(db.String(200))  # 保留文件一的兴趣标签
    major = db.Column(db.String(100))    # 专业（文件一基础，文件二扩展）
    grade = db.Column(db.String(20))     # 年级（文件一基础，文件二扩展）
    # 文件二新增字段
    real_name = db.Column(db.String(50), default='')  # 真实姓名
    student_id = db.Column(db.String(20), default='')  # 学号
    phone = db.Column(db.String(11), default='')       # 手机号
    gender = db.Column(db.String(10), default='')      # 性别
    bio = db.Column(db.String(200), default='')        # 个人简介
    avatar = db.Column(db.String(200), default='/static/avatars/default.jpg')  # 头像
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # 创建时间

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(120), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 学术/体育/艺术/其他
    time = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    tags = db.Column(db.String(200), default='')  # 活动标签，逗号分隔（文件一保留）
    description = db.Column(db.Text, default='')  # 活动描述（文件一保留）
    initiator_id = db.Column(db.String(8), db.ForeignKey('user.id'))  # 发起人ID
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # 创建时间
    # 关联参与者（文件一保留）
    participants = db.relationship('User', secondary='activity_participants', backref=db.backref('joined_activities'))

# 活动-用户多对多关联表（报名关系，文件一保留）
activity_participants = db.Table(
    'activity_participants',
    db.Column('user_id', db.String(8), db.ForeignKey('user.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True)
)

# 收藏关系表（新增，替代文件二的内存字典）
activity_favorites = db.Table(
    'activity_favorites',
    db.Column('user_id', db.String(8), db.ForeignKey('user.id'), primary_key=True),
    db.Column('activity_id', db.Integer, db.ForeignKey('activity.id'), primary_key=True)
)
# 给User添加收藏关联
User.favorite_activities = db.relationship('Activity', secondary=activity_favorites, backref=db.backref('favorited_by'))

# 关注关系表（文件一保留）
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('follower_id', 'followed_id', name='_follower_followed_uc'),)

# 创建数据库表（启动时自动执行）
with app.app_context():
    db.create_all()

# -------------------------- 辅助函数 --------------------------
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

# -------------------------- 页面路由（整合后） --------------------------
# 首页
@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    return render_template('index.html')

# 登录页
@app.route('/login')
def login_page():
    return render_template('login.html')

# 注册页
@app.route('/register')
def register_page():
    return render_template('register.html')

# 个人中心页（文件二新增）
@app.route('/profile')
def profile_page():
    if not is_logged_in():
        return redirect(url_for('login_page'))
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return redirect(url_for('login_page'))
    return render_template("profile.html", user=user)

# 创建活动页（文件一保留）
@app.route('/create-activity')
def create_activity_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('create_activity.html')

# 活动详情页（文件一保留）
@app.route('/activity/<int:activity_id>')
def activity_detail(activity_id):
    activity = Activity.query.get_or_404(activity_id)
    initiator = User.query.get(activity.initiator_id) if activity.initiator_id else None
    return render_template('activity_detail.html', 
                           activity=activity, 
                           initiator=initiator,
                           username=session.get('username'))

# -------------------------- API接口（整合后） --------------------------
# 注册接口（合并文件一和文件二的字段）
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
        
        # 验证用户名长度
        if len(data["username"]) < 3 or len(data["username"]) > 20:
            return jsonify({"success": False, "error": "用户名长度需在3-20个字符之间"}), 400
        
        # 检查用户名和邮箱是否已存在
        if find_user(data["username"]):
            return jsonify({"success": False, "error": "用户名已被注册"}), 409
        if User.query.filter_by(email=data["email"]).first():
            return jsonify({"success": False, "error": "邮箱已存在"}), 409
        
        # 创建新用户（合并字段）
        hashed_password = generate_password_hash(data["password"], method='pbkdf2:sha256')
        new_user = User(
            username=data["username"],
            email=data["email"],
            password=hashed_password,
            hobbies=data.get("hobbies", ""),
            major=data.get("major", ""),
            grade=data.get("grade", ""),
            real_name=data.get("real_name", ""),
            student_id=data.get("student_id", ""),
            phone=data.get("phone", ""),
            gender=data.get("gender", ""),
            bio=data.get("bio", "")
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "注册成功，请登录",
            "data": {"username": new_user.username}
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": f"服务器错误：{str(e)}"}), 500

# 登录接口（整合文件一和文件二）
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
        
        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {"username": user.username, "user_id": user.id}
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"服务器错误：{str(e)}"}), 500

# 注销接口（整合）
@app.route('/api/logout', methods=['POST'])
def logout():
    try:
        session.clear()
        return jsonify({"success": True, "message": "已成功登出"})
    except Exception as e:
        return jsonify({"success": False, "error": f"服务器错误：{str(e)}"}), 500

# 获取当前登录用户信息（整合）
@app.route("/api/current-user", methods=["GET"])
def get_current_user():
    if not is_logged_in():
        return jsonify({"success": False, "error": "未登录"}), 401
    
    return jsonify({
        "success": True,
        "data": {"username": session["username"], "user_id": session["user_id"]}
    })

# -------------------------- 活动API（整合后） --------------------------
# 获取所有活动接口（整合）
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

# 获取单个活动详情（文件二新增接口）
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

# 创建活动接口（整合）
@app.route('/api/activities', methods=['POST'])
def create_activity():
    if not is_logged_in():
        return jsonify({"success": False, "message": "请先登录"}), 401
    
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

# 活动报名接口（整合）
@app.route('/api/activities/<int:activity_id>/join', methods=['POST'])
def join_activity(activity_id: int):
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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

# 取消报名接口（文件二新增）
@app.route("/api/activities/<int:activity_id>/leave", methods=["POST"])
def leave_activity(activity_id: int):
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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

# 活动收藏/取消收藏接口（文件二新增）
@app.route("/api/activities/<int:activity_id>/favorite", methods=["POST"])
def favorite_activity(activity_id: int):
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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

# 活动搜索接口（文件二新增）
@app.route("/api/activities/search", methods=["GET"])
def search_activities():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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

# 活动推荐接口（文件一保留）
@app.route('/api/activities/recommend', methods=['GET'])
def recommend_activities():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
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

# -------------------------- 个人中心API（文件二新增） --------------------------
# 获取用户基本资料
@app.route("/api/user/profile", methods=["GET"])
def get_user_profile():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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
            "created_at": user.created_at,
            "stats": {
                "activities_joined": participated_count,
                "total_activities": total_activities,
                "favorites_count": favorites_count
            },
            "avatar": user.avatar
        }
    })

# 更新用户基本资料（邮箱）
@app.route("/api/user/profile", methods=["PUT"])
def update_user_profile():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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
        user.email = data["email"]
        db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "个人资料更新成功",
        "data": {"username": user.username, "email": user.email}
    })

# 获取用户详细资料
@app.route("/api/user/profile/detailed", methods=["GET"])
def get_detailed_profile():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
    user_id = session["user_id"]
    user = find_user_by_id(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    # 返回所有个人资料字段
    profile_data = {
        "username": user.username,
        "email": user.email,
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
def update_detailed_profile():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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
def get_joined_activities():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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
def get_user_favorites_api():
    if not is_logged_in():
        return jsonify({"success": False, "error": "请先登录"}), 401
    
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

# -------------------------- 运行应用 --------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)