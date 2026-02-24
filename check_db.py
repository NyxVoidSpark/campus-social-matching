import os
import sqlite3

# 检查当前目录
print(f"当前目录: {os.getcwd()}")
print(f"目录内容: {os.listdir('.')}")

# 尝试连接数据库
try:
    conn = sqlite3.connect('campus_social.db')
    print("✅ 成功连接到数据库")
    cursor = conn.cursor()
    
    # 检查所有表
    print("\n所有表:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # 检查用户相关表
    print("\n检查用户数据:")
    if tables:
        # 尝试查询可能的用户表
        possible_user_tables = ['user', 'users']
        for table_name in possible_user_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"{table_name}表有 {count} 条记录")
                
                # 查看前几条记录
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                rows = cursor.fetchall()
                if rows:
                    print(f"{table_name}表前3条记录:")
                    for row in rows:
                        print(f"  - {row}")
            except Exception as e:
                print(f"查询{table_name}表失败: {str(e)}")
    
    conn.close()
except Exception as e:
    print(f"❌ 连接数据库失败: {str(e)}")
