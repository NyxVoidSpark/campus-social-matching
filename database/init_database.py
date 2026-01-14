"""
数据库初始化脚本
用于创建好友和消息相关的表
"""
from app import app, db
from app import Friendship, Message

def init_database():
    """初始化数据库表"""
    with app.app_context():
        # 创建所有表（如果不存在）
        db.create_all()
        print("数据库表创建完成！")
        print("- Friendship 表已创建")
        print("- Message 表已创建")

if __name__ == '__main__':
    init_database()
