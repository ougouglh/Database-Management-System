# -*- coding: utf-8 -*-
"""
SQL 查询构建器 - 使用参数化查询防止 SQL 注入
"""

from typing import List, Tuple, Optional


class QueryBuilder:
    """SQL 查询构建器"""

    # 支持的操作符
    OPERATORS = {
        'eq': '=',
        'ne': '!=',
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        'like': 'LIKE',
        'not_like': 'NOT LIKE',
        'in': 'IN',
        'not_in': 'NOT IN',
        'is_null': 'IS NULL',
        'is_not_null': 'IS NOT NULL',
        'between': 'BETWEEN'
    }

    def build_select(
        self,
        table: str,
        fields: List[str],
        conditions: Optional[List[dict]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Tuple[str, List]:
        """
        构建 SELECT 查询

        Args:
            table: 表名
            fields: 字段列表
            conditions: 条件列表 [{"field": "xxx", "op": "eq", "value": "yyy"}]
            limit: 限制行数
            offset: 偏移量

        Returns:
            (sql, params) 元组
        """
        if not fields:
            fields = ['*']

        # 构建 SELECT 部分
        field_list = ', '.join([f"`{f}`" for f in fields])
        sql = f"SELECT {field_list} FROM `{table}`"
        params = []

        # 构建 WHERE 部分
        if conditions:
            where_sql, where_params = self._build_where(conditions)
            sql += f" WHERE {where_sql}"
            params.extend(where_params)

        # 排序（默认按第一个字段）
        if len(fields) > 0 and fields[0] != '*':
            sql += f" ORDER BY `{fields[0]}`"

        # LIMIT 和 OFFSET
        if limit is not None:
            sql += " LIMIT %s"
            params.append(limit)
            if offset is not None:
                sql += " OFFSET %s"
                params.append(offset)

        return sql, params

    def build_count(
        self,
        table: str,
        conditions: Optional[List[dict]] = None
    ) -> Tuple[str, List]:
        """
        构建 COUNT 查询

        Args:
            table: 表名
            conditions: 条件列表

        Returns:
            (sql, params) 元组
        """
        sql = f"SELECT COUNT(*) as total FROM `{table}`"
        params = []

        if conditions:
            where_sql, where_params = self._build_where(conditions)
            sql += f" WHERE {where_sql}"
            params.extend(where_params)

        return sql, params

    def build_update(
        self,
        table: str,
        field_values: dict,
        conditions: Optional[List[dict]] = None,
        limit: Optional[int] = None
    ) -> Tuple[str, List]:
        """
        构建 UPDATE 查询

        Args:
            table: 表名
            field_values: 要更新的字段和值 {"field1": "value1", "field2": "value2"}
            conditions: WHERE 条件
            limit: 限制更新行数

        Returns:
            (sql, params) 元组
        """
        if not field_values:
            raise ValueError("至少需要一个要更新的字段")

        # 构建 SET 部分
        set_parts = []
        params = []

        for field, value in field_values.items():
            set_parts.append(f"`{field}` = %s")
            params.append(value)

        sql = f"UPDATE `{table}` SET {', '.join(set_parts)}"

        # 构建 WHERE 部分
        if conditions:
            where_sql, where_params = self._build_where(conditions)
            sql += f" WHERE {where_sql}"
            params.extend(where_params)

        # LIMIT（MySQL 支持 UPDATE LIMIT）
        if limit is not None:
            sql += " LIMIT %s"
            params.append(limit)

        return sql, params

    def _build_where(self, conditions: List[dict]) -> Tuple[str, List]:
        """
        构建 WHERE 子句

        Args:
            conditions: 条件列表

        Returns:
            (where_sql, params) 元组
        """
        if not conditions:
            return "", []

        parts = []
        params = []

        for cond in conditions:
            field = cond.get('field', '')
            op = cond.get('op', 'eq')
            value = cond.get('value')

            sql_op = self.OPERATORS.get(op, '=')
            field_sql = f"`{field}`"

            # 处理不同操作符
            if op in ('is_null', 'is_not_null'):
                parts.append(f"{field_sql} {sql_op}")
            elif op in ('in', 'not_in'):
                if isinstance(value, list):
                    placeholders = ', '.join(['%s'] * len(value))
                    parts.append(f"{field_sql} {sql_op} ({placeholders})")
                    params.extend(value)
                else:
                    parts.append(f"{field_sql} {sql_op} (%s)")
                    params.append(value)
            elif op == 'between':
                if isinstance(value, list) and len(value) == 2:
                    parts.append(f"{field_sql} {sql_op} %s AND %s")
                    params.extend(value)
                else:
                    # 无效的 between 参数
                    continue
            else:
                # 普通 =, !=, >, <, LIKE 等
                if op == 'like' or op == 'not_like':
                    # LIKE 操作需要 % 通配符
                    if '%' not in str(value):
                        value = f"%{value}%"
                parts.append(f"{field_sql} {sql_op} %s")
                params.append(value)

        where_sql = ' AND '.join(parts)
        return where_sql, params
