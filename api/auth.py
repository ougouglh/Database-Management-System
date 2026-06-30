#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证相关 API
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import pymysql

from utils.security import verify_password, hash_password, create_access_token, decode_access_token
from utils.db import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["认证"])
security = HTTPBearer()


# ===== 请求/响应模型 =====

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None


class UserInfo(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    email: Optional[str] = None
    role_code: str


# ===== 依赖注入 =====

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    获取当前登录用户

    Args:
        credentials: HTTP Bearer token

    Returns:
        用户信息

    Raises:
        HTTPException: 认证失败
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    # 从数据库获取用户信息
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT id, username, real_name, email, role_code, is_active FROM data_sync_sys_user WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()

        if user is None or not user['is_active']:
            raise HTTPException(status_code=401, detail="用户不存在或已禁用")

        return user
    finally:
        cursor.close()
        conn.close()


def log_operation(conn, user_id: int, username: str, operation_type: str,
                 stage_id: Optional[int] = None, table_name: Optional[str] = None,
                 affected_rows: int = 0, status: str = "success",
                 error_message: Optional[str] = None, ip_address: Optional[str] = None,
                 user_agent: Optional[str] = None):
    """
    记录操作日志

    Args:
        conn: 数据库连接
        user_id: 用户ID
        username: 用户名
        operation_type: 操作类型
        stage_id: 阶段ID
        table_name: 表名
        affected_rows: 影响行数
        status: 状态
        error_message: 错误信息
        ip_address: IP地址
        user_agent: 用户代理
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT INTO data_sync_sys_operation_log
               (user_id, username, operation_type, stage_id, table_name, affected_rows, status, error_message, ip_address, user_agent)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (user_id, username, operation_type, stage_id, table_name, affected_rows, status, error_message, ip_address, user_agent)
        )
        conn.commit()
    finally:
        cursor.close()


# ===== API 端点 =====

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """
    用户登录

    Args:
        request: 登录请求
        req: FastAPI Request 对象

    Returns:
        登录响应，包含 access_token 和用户信息
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 查询用户
        cursor.execute(
            "SELECT id, username, password_hash, real_name, email, role_code, is_active FROM data_sync_sys_user WHERE username = %s",
            (request.username,)
        )
        user = cursor.fetchone()

        # 验证用户
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        if not user['is_active']:
            raise HTTPException(status_code=401, detail="账户已禁用")

        # 验证密码
        if not verify_password(request.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 创建 token
        access_token = create_access_token(
            data={"sub": user['username'], "user_id": user['id']}
        )

        # 记录登录日志
        client_host = req.client.host if req.client else None
        log_operation(
            conn=conn,
            user_id=user['id'],
            username=user['username'],
            operation_type="login",
            ip_address=client_host,
            user_agent=req.headers.get("user-agent")
        )

        # 返回用户信息（不包含密码）
        user_info = {
            "id": user['id'],
            "username": user['username'],
            "real_name": user['real_name'],
            "email": user['email'],
            "role_code": user['role_code']
        }

        return LoginResponse(
            access_token=access_token,
            user=user_info
        )

    finally:
        cursor.close()
        conn.close()


@router.post("/logout")
async def logout(req: Request, current_user: dict = Depends(get_current_user)):
    """
    用户登出（前端需删除 token）

    Args:
        current_user: 当前用户
        req: FastAPI Request 对象

    Returns:
        登出成功消息
    """
    conn = get_db_connection()

    try:
        # 记录登出日志
        client_host = req.client.host if req.client else None
        log_operation(
            conn=conn,
            user_id=current_user['id'],
            username=current_user['username'],
            operation_type="logout",
            ip_address=client_host,
            user_agent=req.headers.get("user-agent")
        )

        return {"success": True, "message": "登出成功"}
    finally:
        conn.close()


@router.get("/info", response_model=UserInfo)
async def get_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前用户信息

    Args:
        current_user: 当前用户

    Returns:
        用户信息
    """
    return UserInfo(
        id=current_user['id'],
        username=current_user['username'],
        real_name=current_user['real_name'],
        email=current_user['email'],
        role_code=current_user['role_code']
    )


@router.get("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    验证 token 是否有效

    Args:
        current_user: 当前用户

    Returns:
        验证结果
    """
    return {
        "success": True,
        "valid": True,
        "user": {
            "id": current_user['id'],
            "username": current_user['username'],
            "role_code": current_user['role_code']
        }
    }
