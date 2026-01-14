# 校园社交匹配与活动平台（示例实现）

此仓库实现了一个「校园活动 + 分类信息 + 好友 & 私聊」的示例应用，包含：

- 活动与信息发布：
  - 7 大核心场景分区：教学科研、校园活动、生活服务、求职就业、学术交流、兴趣社群、求助问答
  - 结构化发布：支持标题、正文、标签、文件/图片/视频上传
  - 官方认证：用户可申请官方认证（管理员审核后生效），被认证的账号可以发布“官方”信息，展示为红色“官方”标识
- 社交能力：
  - 好友管理：搜索用户、发送好友请求、处理请求、查看/删除好友
  - 消息中心：与好友一对一聊天，会话列表、未读数、历史记录展示
  - 首页右上角整合入口：一键进入“好友”和“消息”页面

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

3. 初始化数据库（可选，首次运行或表不存在时）：
   - 方式一（推荐）：
   ```powershell
   python database\init_database.py
   ```
   - 方式二（直接执行 SQL）：
   ```powershell
   mysql -u root -p campus_social < database\create_tables.sql
   ```

4. 运行服务：
```powershell
python app.py
```

5. 打开浏览器访问（默认端口可能为 5001，请以控制台实际输出为准）：
   - 登录页：`http://127.0.0.1:5001/login`
   - 首页：`http://127.0.0.1:5001/`

6. 好友 & 消息入口：
   - 登录成功后进入首页，右上角有：
     - **好友**：跳转到 `/friends?tab=search`，默认打开“添加好友”标签页
     - **消息**：跳转到 `/messages`，进入消息中心

测试（假设已安装 pytest）：
```powershell
python -m pytest -q tests/test_posts.py
```

说明（部分）：
- 实际运行使用 MySQL 数据库（连接配置见 `app.py` 中的 `SQLALCHEMY_DATABASE_URI`），请根据本地环境调整 `.env`。
- 上传的文件保存在 `static/uploads/`，头像保存在 `static/uploads/avatars/`。
- 更多关于好友与消息功能的详细说明，见 `QUICK_START.md`。
