#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建用户脚本
使用方法: python create_user.py 用户名 密码 [角色] [姓名]
"""

import sys
import pymysql
import yaml
from utils.security import hash_password

def load_config():
    """加载配置"""
    with open('config.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_user(username, password, role_code='viewer', real_name=None):
    """创建用户"""
    config = load_config()
    db_config = config['mysql1']

    conn = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset']
    )
    cursor = conn.cursor()

    try:
        # 检查用户是否存在
        cursor.execute("SELECT id FROM data_sync_sys_user WHERE username = %s", (username,))
        if cursor.fetchone():
            print(f"用户 '{username}' 已存在")
            return False

        # 创建用户
        password_hash = hash_password(password)
        sql = """
            INSERT INTO data_sync_sys_user (username, password_hash, real_name, role_code, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
        """
        cursor.execute(sql, (username, password_hash, real_name, role_code))
        conn.commit()

        print(f"用户 '{username}' 创建成功")
        print(f"  密码: {password}")
        print(f"  角色: {role_code}")
        print(f"  姓名: {real_name or '未设置'}")
        return True

    except Exception as e:
        conn.rollback()
        print(f"创建用户失败: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def list_users():
    """列出所有用户"""
    config = load_config()
    db_config = config['mysql1']

    conn = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset']
    )
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, username, real_name, role_code, is_active, created_at
            FROM data_sync_sys_user
            ORDER BY id
        """)

        users = cursor.fetchall()
        if not users:
            print("暂无用户")
            return

        print("\n用户列表:")
        print("-" * 70)
        print(f"{'ID':<5} {'用户名':<15} {'姓名':<15} {'角色':<15} {'状态':<8}")
        print("-" * 70)
        for user in users:
            print(f"{user['id']:<5} {user['username']:<15} {(user['real_name'] or '-'):<15} {user['role_code']:<15} {'启用' if user['is_active'] else '禁用':<8}")

    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  创建用户: python create_user.py <用户名> <密码> [角色] [姓名]")
        print("  列出用户: python create_user.py --list")
        print("\n示例:")
        print("  python create_user.py zhangsan 123456 viewer 张三")
        print("  python create_user.py --list")
        list_users()
        sys.exit(0)

    if sys.argv[1] == '--list':
        list_users()
        sys.exit(0)

    if len(sys.argv) < 3:
        print("错误: 请提供用户名和密码")
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    role_code = sys.argv[3] if len(sys.argv) > 3 else 'viewer'
    real_name = sys.argv[4] if len(sys.argv) > 4 else None

    create_user(username, password, role_code, real_name)
