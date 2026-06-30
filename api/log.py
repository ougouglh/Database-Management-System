#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作日志相关 API
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import pymysql

from utils.db import get_db_connection
from api.auth import get_current_user

router = APIRouter(prefix="/api/logs", tags=["操作日志"])


# ===== 请求/响应模型 =====

class LogEntry(BaseModel):
    id: int
    user_id: int
    username: str
    operation_type: str
    stage_id: Optional[int] = None
    table_name: Optional[str] = None
    affected_rows: int = 0
    status: str
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


class LogListResponse(BaseModel):
    success: bool
    data: List[LogEntry]
    total: int
    page: int
    pageSize: int


# ===== API 端点 =====

@router.get("/operations", response_model=LogListResponse)
async def get_operation_logs(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(50, ge=1, le=100, description="每页记录数"),
    operation_type: Optional[str] = Query(None, description="操作类型"),
    stage_id: Optional[int] = Query(None, description="阶段ID"),
    username: Optional[str] = Query(None, description="用户名"),
    status: Optional[str] = Query(None, description="状态：success/failed"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取操作日志列表

    Args:
        page: 页码
        pageSize: 每页记录数
        operation_type: 操作类型筛选
        stage_id: 阶段ID筛选
        username: 用户名筛选
        status: 状态筛选
        current_user: 当前用户

    Returns:
        日志列表
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 构建查询条件
        where_conditions = []
        params = []

        if operation_type:
            where_conditions.append("operation_type = %s")
            params.append(operation_type)

        if stage_id is not None:
            where_conditions.append("stage_id = %s")
            params.append(stage_id)

        if username:
            where_conditions.append("username LIKE %s")
            params.append(f"%{username}%")

        if status:
            where_conditions.append("status = %s")
            params.append(status)

        where_clause = ""
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)

        # 获取总数
        count_sql = f"SELECT COUNT(*) as total FROM data_sync_sys_operation_log{where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']

        # 获取分页数据
        offset = (page - 1) * pageSize
        data_sql = f"""
            SELECT id, user_id, username, operation_type, stage_id, table_name,
                   affected_rows, status, error_message, ip_address, created_at
            FROM data_sync_sys_operation_log
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(data_sql, params + [pageSize, offset])
        data = cursor.fetchall()

        return LogListResponse(
            success=True,
            data=data,
            total=total,
            page=page,
            pageSize=pageSize
        )

    finally:
        cursor.close()
        conn.close()


@router.get("/stats")
async def get_log_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    获取操作日志统计信息

    Args:
        current_user: 当前用户

    Returns:
        统计数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 今日操作统计
        cursor.execute("""
            SELECT operation_type, status, COUNT(*) as count
            FROM data_sync_sys_operation_log
            WHERE DATE(created_at) = CURDATE()
            GROUP BY operation_type, status
        """)
        today_stats = cursor.fetchall()

        # 总操作数
        cursor.execute("SELECT COUNT(*) as total FROM data_sync_sys_operation_log")
        total_operations = cursor.fetchone()['total']

        # 按类型统计
        cursor.execute("""
            SELECT operation_type, COUNT(*) as count
            FROM data_sync_sys_operation_log
            GROUP BY operation_type
        """)
        type_stats = cursor.fetchall()

        return {
            "success": True,
            "today_stats": today_stats,
            "total_operations": total_operations,
            "type_stats": type_stats
        }

    finally:
        cursor.close()
        conn.close()
