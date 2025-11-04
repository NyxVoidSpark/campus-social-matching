from flask import Flask, render_template

app = Flask(__name__)

# 添加根路径路由
@app.route("/")
def home():
    return "欢迎访问高校信息聚合平台首页"

# 现有的路由
@app.route("/show/info")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)