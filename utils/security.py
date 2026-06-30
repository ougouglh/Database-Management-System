#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全相关工具函数
"""

import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

# 加载配置
def load_config():
    """加载配置文件"""
    import yaml
    import os
    config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        # 如果配置文件不存在，返回默认配置
        return {
            'auth': {
                'secret_key': 'your-secret-key-change-in-production',
                'algorithm': 'HS256',
                'access_token_expire_minutes': 480
            }
        }

config = load_config()
auth_config = config.get('auth', {})

# JWT 配置
SECRET_KEY = auth_config.get('secret_key', 'your-secret-key-change-in-production')
ALGORITHM = auth_config.get('algorithm', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = auth_config.get('access_token_expire_minutes', 480)


def hash_password(password: str) -> str:
    """
    对密码进行哈希加密

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        是否匹配
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌

    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量

    Returns:
        JWT token 字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict]:
    """
    解码 JWT 访问令牌

    Args:
        token: JWT token 字符串

    Returns:
        解码后的数据，失败返回 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
