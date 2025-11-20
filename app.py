from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from typing import List, Dict, Optional, Any

# 初始化Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 模拟数据库 - 活动数据
activities: List[Dict[str, Any]] = [
    {"id": 1, "title": "Java编程竞赛", "type": "学术", "time": "2025-04-15", "location": "计算机学院实验室",
     "participants": []},
    {"id": 2, "title": "校园篮球联赛", "type": "体育", "time": "2025-04-20", "location": "体育馆", "participants": []},
    {"id": 3, "title": "摄影技巧分享会", "type": "艺术", "time": "2025-04-18", "location": "艺术楼201",
     "participants": []}
]


# 辅助函数：查找活动
def find_activity(activity_id: int) -> Optional[Dict[str, Any]]:
    """根据ID查找活动"""
    return next((a for a in activities if a["id"] == activity_id), None)


# 页面路由
@app.route("/")
@app.route("/show/info")
def home() -> str:
    """首页路由，合并了重复的路由定义"""
    return render_template("index.html")


# API路由：获取所有活动
@app.route("/api/activities", methods=["GET"])
def get_activities() -> Any:
    """获取所有活动列表"""
    return jsonify({
        "success": True,
        "data": activities,
        "count": len(activities)
    })


# API路由：根据ID获取单个活动
@app.route("/api/activities/<int:activity_id>", methods=["GET"])
def get_activity(activity_id: int) -> Any:
    """根据ID获取单个活动详情"""
    activity = find_activity(activity_id)
    if activity:
        return jsonify({
            "success": True,
            "data": activity
        })
    return jsonify({
        "success": False,
        "error": "活动不存在"
    }), 404


# API路由：创建新活动
@app.route("/api/activities", methods=["POST"])
def create_activity() -> Any:
    """创建新活动"""
    if not request.json:
        return jsonify({
            "success": False,
            "error": "请求数据为空或格式不正确"
        }), 400

    required_fields = ["title", "type", "time", "location"]
    for field in required_fields:
        if field not in request.json:
            return jsonify({
                "success": False,
                "error": f"缺少必要字段: {field}"
            }), 400

    # 生成新ID
    new_id = max(activity["id"] for activity in activities) + 1 if activities else 1

    new_activity = {
        "id": new_id,
        "title": request.json["title"],
        "type": request.json["type"],
        "time": request.json["time"],
        "location": request.json["location"],
        "participants": []
    }

    activities.append(new_activity)
    return jsonify({
        "success": True,
        "message": "活动创建成功",
        "data": new_activity
    }), 201


# API路由：参加活动（报名逻辑）
@app.route("/api/activities/<int:activity_id>/join", methods=["POST"])
def join_activity(activity_id: int) -> Any:
    """参加活动"""
    activity = find_activity(activity_id)
    if not activity:
        return jsonify({
            "success": False,
            "error": "活动不存在"
        }), 404

    # 获取用户信息（实际应用中应从认证系统获取）
    user_info = request.json.get("user", {"id": "anonymous", "name": "匿名用户"})

    # 检查是否已报名
    if any(p["id"] == user_info["id"] for p in activity["participants"]):
        return jsonify({
            "success": False,
            "error": "您已报名该活动"
        }), 400

    activity["participants"].append(user_info)
    return jsonify({
        "success": True,
        "message": f"成功报名活动: {activity['title']}",
        "data": {
            "activity_id": activity_id,
            "participants_count": len(activity["participants"])
        }
    })


# API路由：取消参加活动
@app.route("/api/activities/<int:activity_id>/leave", methods=["POST"])
def leave_activity(activity_id: int) -> Any:
    """取消参加活动"""
    activity = find_activity(activity_id)
    if not activity:
        return jsonify({
            "success": False,
            "error": "活动不存在"
        }), 404

    user_info = request.json.get("user", {"id": "anonymous"})

    # 查找并移除参与者
    for i, participant in enumerate(activity["participants"]):
        if participant["id"] == user_info["id"]:
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


if __name__ == '__main__':
    app.run(debug=True)