from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from datetime import datetime

# 初始化Flask应用
app = Flask(__name__)
CORS(app, supports_credentials=True)  # 支持跨域请求携带cookie

# 配置
app.secret_key = 'your-secret-key-keep-it-safe'  # 生产环境请更换为随机密钥
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24 * 7  # Session有效期7天

# -------------------------- 数据存储（内存模拟数据库） --------------------------
# 用户数据
users = [
    {
        "id": "1",
        "username": "admin",
        "password": generate_password_hash("123456"),
        "email": "admin@example.com",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

# 活动数据
activities = [
    {
        "id": 1,
        "title": "Java编程竞赛",
        "type": "学术",
        "time": "2025-04-15",
        "location": "计算机学院实验室",
        "participants": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 2,
        "title": "校园篮球联赛",
        "type": "体育",
        "time": "2025-04-20",
        "location": "体育馆",
        "participants": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    },
    {
        "id": 3,
        "title": "摄影技巧分享会",
        "type": "艺术",
        "time": "2025-04-18",
        "location": "艺术楼201",
        "participants": [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]


# -------------------------- 辅助函数 --------------------------
def find_user(username):
    """根据用户名查找用户"""
    return next((u for u in users if u["username"] == username), None)


def find_user_by_id(user_id):
    """根据ID查找用户"""
    return next((u for u in users if u["id"] == user_id), None)


def is_logged_in():
    """检查用户是否已登录"""
    return "user_id" in session


def get_next_activity_id():
    """获取下一个活动ID"""
    return max(activity["id"] for activity in activities) + 1 if activities else 1


# -------------------------- 页面路由 --------------------------
@app.route("/")
def home():
    """首页路由"""
    if not is_logged_in():
        return redirect(url_for('login_page'))
    return render_template("index.html")


@app.route("/login")
def login_page():
    """登录页面"""
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template("login.html")


@app.route("/register")
def register_page():
    """注册页面"""
    if is_logged_in():
        return redirect(url_for('home'))
    return render_template("register.html")


# -------------------------- 认证API --------------------------
@app.route("/api/register", methods=["POST"])
def register():
    """用户注册API"""
    try:
        # 检查请求格式
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "请求格式必须为JSON"
            }), 400

        data = request.get_json()

        # 验证必填字段
        required_fields = ["username", "password", "email"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "success": False,
                    "error": f"缺少字段：{field}"
                }), 400

        # 验证用户名长度
        if len(data["username"]) < 3 or len(data["username"]) > 20:
            return jsonify({
                "success": False,
                "error": "用户名长度需在3-20个字符之间"
            }), 400

        # 检查用户名是否已存在
        if find_user(data["username"]):
            return jsonify({
                "success": False,
                "error": "用户名已被注册"
            }), 409

        # 创建新用户
        new_user = {
            "id": str(uuid.uuid4())[:8],
            "username": data["username"],
            "password": generate_password_hash(data["password"]),
            "email": data["email"],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        users.append(new_user)

        return jsonify({
            "success": True,
            "message": "注册成功，请登录",
            "data": {"username": new_user["username"]}
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route("/api/login", methods=["POST"])
def login():
    """用户登录API"""
    try:
        # 检查请求格式
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "请求格式必须为JSON"
            }), 400

        data = request.get_json()

        # 验证输入
        if not data or "username" not in data or not data["username"]:
            return jsonify({
                "success": False,
                "error": "请输入用户名"
            }), 400

        if "password" not in data or not data["password"]:
            return jsonify({
                "success": False,
                "error": "请输入密码"
            }), 400

        # 查找用户
        user = find_user(data["username"])
        if not user:
            return jsonify({
                "success": False,
                "error": "用户名或密码错误"
            }), 401

        # 验证密码
        if not check_password_hash(user["password"], data["password"]):
            return jsonify({
                "success": False,
                "error": "用户名或密码错误"
            }), 401

        # 登录成功，记录session
        session.permanent = True
        session["user_id"] = user["id"]
        session["username"] = user["username"]

        return jsonify({
            "success": True,
            "message": "登录成功",
            "data": {
                "username": user["username"],
                "user_id": user["id"]
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    """用户登出API"""
    try:
        session.clear()
        return jsonify({
            "success": True,
            "message": "已成功登出"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route("/api/current-user", methods=["GET"])
def get_current_user():
    """获取当前登录用户信息"""
    if not is_logged_in():
        return jsonify({
            "success": False,
            "error": "未登录"
        }), 401

    return jsonify({
        "success": True,
        "data": {
            "username": session["username"],
            "user_id": session["user_id"]
        }
    })


# -------------------------- 活动API --------------------------
@app.route("/api/activities", methods=["GET"])
def get_activities():
    """获取所有活动"""
    try:
        return jsonify({
            "success": True,
            "data": activities,
            "count": len(activities)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route("/api/activities/<int:activity_id>", methods=["GET"])
def get_activity(activity_id):
    """获取单个活动详情"""
    try:
        activity = next((a for a in activities if a["id"] == activity_id), None)

        if activity:
            return jsonify({
                "success": True,
                "data": activity
            })
        return jsonify({
            "success": False,
            "error": "活动不存在"
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route("/api/activities/<int:activity_id>/join", methods=["POST"])
def join_activity(activity_id):
    """参加活动"""
    try:
        if not is_logged_in():
            return jsonify({
                "success": False,
                "error": "请先登录"
            }), 401

        activity = next((a for a in activities if a["id"] == activity_id), None)

        if not activity:
            return jsonify({
                "success": False,
                "error": "活动不存在"
            }), 404

        # 获取当前登录用户信息
        current_user = {
            "id": session["user_id"],
            "name": session["username"]
        }

        # 检查是否已报名
        if any(p["id"] == current_user["id"] for p in activity["participants"]):
            return jsonify({
                "success": False,
                "error": "您已报名该活动"
            }), 400

        # 添加参与者
        activity["participants"].append(current_user)

        return jsonify({
            "success": True,
            "message": f"成功报名活动: {activity['title']}",
            "data": {
                "activity_id": activity_id,
                "participants_count": len(activity["participants"])
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


@app.route("/api/activities/<int:activity_id>/leave", methods=["POST"])
def leave_activity(activity_id):
    """取消参加活动"""
    try:
        if not is_logged_in():
            return jsonify({
                "success": False,
                "error": "请先登录"
            }), 401

        activity = next((a for a in activities if a["id"] == activity_id), None)

        if not activity:
            return jsonify({
                "success": False,
                "error": "活动不存在"
            }), 404

        # 查找并移除参与者
        user_id = session["user_id"]
        for i, participant in enumerate(activity["participants"]):
            if participant["id"] == user_id:
                activity["participants"].pop(i)
                return jsonify({
                    "success": True,
                    "message": f"已取消报名活动: {activity['title']}",
                    "data": {
                        "activity_id": activity_id,
                        "participants_count": len(activity["participants"])
                    }
                })

        return jsonify({
            "success": False,
            "error": "您未报名该活动"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"服务器错误：{str(e)}"
        }), 500


# -------------------------- 运行应用 --------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)