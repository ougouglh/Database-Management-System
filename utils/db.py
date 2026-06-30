#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库连接工具
"""

import yaml
import pymysql


# 加载配置
def load_config(config_file: str = "config.yaml") -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


config = load_config()
db_config = config['mysql1']


def get_db_connection():
    """
    获取数据库连接

    Returns:
        数据库连接对象
    """
    return pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )
