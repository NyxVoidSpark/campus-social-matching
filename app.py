from flask import Flask, render_template, jsonify, request
from flask_cors import CORS  # 解决跨域问题

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 模拟活动数据（后续可替换为数据库）
activities = [
    {"id": 1, "title": "Java编程竞赛", "type": "学术", "time": "2025-04-15", "location": "计算机学院实验室"},
    {"id": 2, "title": "校园篮球联赛", "type": "体育", "time": "2025-04-20", "location": "体育馆"},
    {"id": 3, "title": "摄影技巧分享会", "type": "艺术", "time": "2025-04-18", "location": "艺术楼201"}
]

# 根路径路由（访问http://127.0.0.1:5000直接加载页面）
@app.route("/")
def home():
    return render_template("index.html")

# 原有页面路由（保留，可通过http://127.0.0.1:5000/show/info访问）
@app.route("/show/info")
def index():
    return render_template("index.html")

# API路由：获取所有活动数据
@app.route("/api/activities")
def get_activities():
    return jsonify(activities)

# API路由：根据ID获取单个活动
@app.route("/api/activities/<int:activity_id>")
def get_activity(activity_id):
    activity = next((a for a in activities if a["id"] == activity_id), None)
    if activity:
        return jsonify(activity)
    return jsonify({"error": "活动不存在"}), 404

# API路由：参加活动（报名逻辑）
@app.route("/api/activities/<int:activity_id>/join", methods=["POST"])
def join_activity(activity_id):
    # 后续可扩展：添加用户验证、报名记录存储等逻辑
    return jsonify({"message": f"成功报名活动 {activity_id} - {next((a['title'] for a in activities if a['id'] == activity_id), '未知活动')}"})

if __name__ == '__main__':
    app.run(debug=True)