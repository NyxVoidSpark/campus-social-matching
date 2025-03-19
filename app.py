# -*- coding: utf-8 -*
from flask import Flask

app = Flask(__name__)


#创建了网址/show/info 和函数index的对应关系
#以后用户在浏览器上访问/show/info,网站自动执行 index
@app.route("/show/info")
def index():
    return "面向高校生态的多元交互信息聚合平台设计与实现"



if __name__=='__main__':
    app.run(debug=True)