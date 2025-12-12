# 校园分类信息发布与展示（示例实现）

此仓库已实现一个简化的「分类信息/公告/发布」功能示例，包含：

- 7 大核心场景分区：教学科研、校园活动、生活服务、求职就业、学术交流、兴趣社群、求助问答
- 结构化发布：支持标题、正文、标签、文件/图片/视频上传
- 官方认证：用户可申请官方认证（管理员审核后生效），被认证的账号可以发布“官方”信息，展示为红色“官方”标识

快速上手（开发环境）：

1. 创建并激活 Python 虚拟环境（Windows PowerShell）：
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

2. 安装依赖：
```powershell
python -m pip install -r requirements.txt
```

3. 运行服务：
```powershell
python app.py
```

4. 打开浏览器访问：http://127.0.0.1:5000 （需要先注册或使用内置 admin 用户）

测试（假设已安装 pytest）：
```powershell
python -m pytest -q tests/test_posts.py
```

说明：
- 当前实现以内存存储（示例）为主，生产应改为持久化数据库（已包含 `database_setup.py` 作为参考 SQLAlchemy 模型）。
- 上传的文件保存在项目根目录的 `uploads/`，通过 `/uploads/<filename>` 提供。生产环境请使用云存储或受控的静态文件服务。
