# -*- coding: utf-8 -*-
"""
SQL 安全校验器 - 防止 SQL 注入和非法操作
"""

import pymysql
from typing import List, Set, Optional
import threading


class SQLValidator:
    """SQL 安全校验器"""

    # 缓存表名和字段名
    _tables_cache: Optional[Set[str]] = None
    _columns_cache: dict = {}
    _cache_lock = threading.Lock()
    _last_refresh: float = 0
    _cache_ttl: int = 300  # 缓存5分钟

    def __init__(self, db_config: dict):
        self.db_config = db_config

    def _get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            charset=self.db_config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )

    def _refresh_cache_if_needed(self):
        """刷新缓存（如果需要）"""
        import time
        now = time.time()

        with self._cache_lock:
            if (self._tables_cache is None or
                now - self._last_refresh > self._cache_ttl):
                self._load_metadata()
                self._last_refresh = now

    def _load_metadata(self):
        """加载表和字段的元数据"""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 加载所有表名
            cursor.execute("""
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                AND TABLE_TYPE = 'BASE TABLE'
            """, (self.db_config['database'],))

            self._tables_cache = {row['TABLE_NAME'] for row in cursor.fetchall()}

            # 加载所有字段
            self._columns_cache = {}
            for table in self._tables_cache:
                cursor.execute("""
                    SELECT COLUMN_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                    AND TABLE_NAME = %s
                """, (self.db_config['database'], table))

                self._columns_cache[table] = {
                    row['COLUMN_NAME'] for row in cursor.fetchall()
                }

            cursor.close()
        except Exception as e:
            print(f"[SQLValidator] 加载元数据失败: {e}")
            self._tables_cache = set()
            self._columns_cache = {}
        finally:
            if conn:
                conn.close()

    def validate_table_name(self, table: str) -> bool:
        """
        验证表名是否合法

        Args:
            table: 表名

        Returns:
            是否合法
        """
        if not table or not isinstance(table, str):
            return False

        # 基本字符检查
        if not table.replace('_', '').replace('-', '').isalnum():
            return False

        self._refresh_cache_if_needed()

        return table in self._tables_cache

    def validate_field_names(self, table: str, fields: List[str]) -> bool:
        """
        验证字段名是否合法

        Args:
            table: 表名
            fields: 字段列表

        Returns:
            是否全部合法
        """
        if not fields:
            return True

        self._refresh_cache_if_needed()

        if table not in self._columns_cache:
            return False

        table_columns = self._columns_cache[table]

        for field in fields:
            if field == '*':
                continue
            if field not in table_columns:
                return False

        return True

    def validate_limit(self, limit: int) -> bool:
        """
        验证 limit 是否在合法范围内

        Args:
            limit: 限制行数

        Returns:
            是否合法
        """
        if not isinstance(limit, int):
            return False
        return 0 < limit <= 100000

    def validate_export_limit(self, limit: int) -> bool:
        """
        验证导出限制（导出最多 100000 条）

        Args:
            limit: 限制行数

        Returns:
            是否合法
        """
        if not isinstance(limit, int):
            return False
        return 0 < limit <= 100000

    def get_tables(self) -> List[str]:
        """
        获取所有表名列表

        Returns:
            表名列表（排序后）
        """
        try:
            self._refresh_cache_if_needed()
            if self._tables_cache:
                return sorted(list(self._tables_cache))
            return []
        except Exception as e:
            print(f"[SQLValidator] get_tables 失败: {e}")
            return []

    def get_columns(self, table: str) -> List[dict]:
        """
        获取表的字段信息

        Args:
            table: 表名

        Returns:
            字段信息列表
        """
        self._refresh_cache_if_needed()

        if table not in self._columns_cache:
            return []

        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (self.db_config['database'], table))

            return list(cursor.fetchall())
        finally:
            if conn:
                conn.close()
