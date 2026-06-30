#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内网数据导入导出系统 - FastAPI 后端
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import pymysql
import yaml
import os
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from data_validator import DataValidator, ValidationLevel
from data_tools import QueryBuilder, SQLValidator

# ===== Load Configuration =====
def load_config(config_file: str = "config.yaml") -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()
db_config = config['mysql1']
auth_config = config.get('auth', {})
upload_config = config.get('upload', {'max_file_size_mb': 50})
export_config = config.get('export', {'max_rows': 100000, 'file_retention_days': 7})

# ===== Database Connection =====
def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset'],
        cursorclass=pymysql.cursors.DictCursor
    )

# ===== FastAPI App =====
app = FastAPI(
    title="内网数据导入导出系统",
    description="barcode_base_info_69_top96_incre_allplatform_name 表数据管理系统",
    version="1.0.0"
)

# ===== Include Routers =====
from api.auth import router as auth_router
from api.log import router as log_router

app.include_router(auth_router)
app.include_router(log_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ===== Query Builder & Validator =====
query_builder = QueryBuilder()
sql_validator = SQLValidator(db_config)

# ===== Request Models =====
class Condition(BaseModel):
    field: str
    op: str = "eq"  # eq, ne, gt, gte, lt, lte, like, not_like, in, not_in, is_null, is_not_null, between
    value: Optional[str] = None

class QueryRequest(BaseModel):
    table: str
    fields: List[str]
    conditions: Optional[List[Condition]] = None
    limit: int = 10000
    offset: Optional[int] = None

class UpdateRequest(BaseModel):
    table: str
    field_values: dict  # {"field1": "value1", "field2": "value2"}
    conditions: Optional[List[Condition]] = None
    limit: Optional[int] = None
    force_no_where: bool = False  # 强制执行无 WHERE 的更新

# ===== API Endpoints =====

@app.get("/", response_class=HTMLResponse)
async def root():
    """主页 - 返回登录页面"""
    login_file = static_dir / "login.html"
    with open(login_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/main", response_class=HTMLResponse)
async def main():
    """主页面 - 返回 HTML 界面（需要登录）"""
    index_file = static_dir / "index.html"
    with open(index_file, 'r', encoding='utf-8') as f:
        return f.read()

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "database": db_config['database']
    }

@app.post("/api/validate")
async def validate_data(file: UploadFile = File(...)):
    """
    数据校验 - 上传文件后预览校验结果，但不导入

    支持的文件格式: .xlsx, .xls, .csv
    必须包含列: item_barcode, new_name
    """
    try:
        import io

        # 读取文件内容到内存
        content = await file.read()

        # 检查文件大小
        max_size = upload_config.get('max_file_size_mb', 50) * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大允许 {upload_config.get('max_file_size_mb', 50)}MB"
            )

        file_obj = io.BytesIO(content)

        file_extension = file.filename.split('.')[-1].lower()

        if file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')
        elif file_extension == 'csv':
            df = pd.read_csv(file_obj, encoding='utf-8-sig')
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 Excel 或 CSV 文件")

        required_columns = ['item_barcode', 'new_name']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"文件缺少必需的列: {', '.join(missing_columns)}"
            )

        df = df[required_columns]
        df = df.dropna(subset=['item_barcode'])

        df = df.rename(columns={'new_name': 'item_name'})

        validator = DataValidator()
        errors, warnings, infos, results = validator.validate_dataframe(df)

        error_list = [
            {
                "row": r.row,
                "field": r.field,
                "value": r.value[:50] + "..." if len(r.value) > 50 else r.value,
                "message": r.message,
                "level": r.level.value
            }
            for r in results if r.level == ValidationLevel.ERROR
        ][:10]

        warning_list = [
            {
                "row": r.row,
                "field": r.field,
                "value": r.value[:50] + "..." if len(r.value) > 50 else r.value,
                "message": r.message,
                "level": r.level.value
            }
            for r in results if r.level == ValidationLevel.WARNING
        ][:10]

        return {
            "success": True,
            "total": len(df),
            "errors": errors,
            "warnings": warnings,
            "infos": infos,
            "errorDetails": error_list,
            "warningDetails": warning_list,
            "canImport": errors == 0
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"校验错误详情: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"校验失败: {str(e)}")

@app.post("/api/preview")
async def preview_changes(file: UploadFile = File(...)):
    """
    变更预览 - 上传文件后预览新增/更新/跳过的记录

    支持的文件格式: .xlsx, .xls, .csv
    必须包含列: item_barcode, new_name
    """
    try:
        import io

        # 读取文件内容到内存
        content = await file.read()

        # 检查文件大小
        max_size = upload_config.get('max_file_size_mb', 50) * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大允许 {upload_config.get('max_file_size_mb', 50)}MB"
            )

        file_obj = io.BytesIO(content)

        file_extension = file.filename.split('.')[-1].lower()

        if file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')
        elif file_extension == 'csv':
            df = pd.read_csv(file_obj, encoding='utf-8-sig')
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")

        # 验证列名
        required_columns = ['item_barcode', 'new_name']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"文件缺少必需的列: {', '.join(missing_columns)}"
            )

        df = df[required_columns]
        df = df.dropna(subset=['item_barcode'])

        # 连接数据库查询现有数据
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取上传文件中的所有条码
        barcodes = [str(row['item_barcode']).strip() for _, row in df.iterrows()]

        # 查询数据库中已有的数据
        if barcodes:
            placeholders = ','.join(['%s'] * len(barcodes))
            sql = f"""
                SELECT item_barcode, item_name, new_name, new_cat_name
                FROM barcode_base_info_69_top96_incre_allplatform_name
                WHERE item_barcode IN ({placeholders})
            """
            cursor.execute(sql, barcodes)
            existing_data = {row[0]: {
                'item_name': row[1],
                'new_name': row[2],
                'new_cat_name': row[3]
            } for row in cursor.fetchall()}
        else:
            existing_data = {}

        cursor.close()
        conn.close()

        # 对比数据并分类
        changes = []
        to_add = 0
        to_update = 0
        to_skip = 0

        for _, row in df.iterrows():
            item_barcode = str(row['item_barcode']).strip()
            new_name = str(row['new_name']).strip() if pd.notna(row['new_name']) else ''

            if item_barcode in existing_data:
                existing = existing_data[item_barcode]
                old_name = existing.get('new_name', '') or existing.get('item_name', '')

                # 检查是否有变化
                if new_name and new_name != old_name:
                    changes.append({
                        'item_barcode': item_barcode,
                        'action': 'update',
                        'old_name': old_name,
                        'new_name': new_name,
                        'new_cat_name': existing.get('new_cat_name', ''),
                        'status': 'success'
                    })
                    to_update += 1
                else:
                    changes.append({
                        'item_barcode': item_barcode,
                        'action': 'skip',
                        'old_name': old_name,
                        'new_name': new_name,
                        'new_cat_name': existing.get('new_cat_name', ''),
                        'status': 'info'
                    })
                    to_skip += 1
            else:
                changes.append({
                    'item_barcode': item_barcode,
                    'action': 'add',
                    'old_name': '',
                    'new_name': new_name,
                    'new_cat_name': '',
                    'status': 'success'
                })
                to_add += 1

        return {
            'success': True,
            'total': len(df),
            'toAdd': to_add,
            'toUpdate': to_update,
            'toSkip': to_skip,
            'changes': changes[:100]  # 返回前100条预览
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"预览错误详情: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"预览失败: {str(e)}")

@app.post("/api/import")
async def import_data(file: UploadFile = File(...)):
    """
    导入数据

    支持的文件格式: .xlsx, .xls, .csv
    必须包含列: item_barcode, new_name
    导入时仅更新 new_name 字段，其他字段保持不变
    """
    try:
        import io

        # 读取文件内容到内存
        content = await file.read()

        # 检查文件大小
        max_size = upload_config.get('max_file_size_mb', 50) * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"文件过大，最大允许 {upload_config.get('max_file_size_mb', 50)}MB"
            )

        file_obj = io.BytesIO(content)

        file_extension = file.filename.split('.')[-1].lower()

        if file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(file_obj, engine='openpyxl' if file_extension == 'xlsx' else 'xlrd')
        elif file_extension == 'csv':
            df = pd.read_csv(file_obj, encoding='utf-8-sig')
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传 Excel 或 CSV 文件")

        # 验证列名
        required_columns = ['item_barcode', 'new_name']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"文件缺少必需的列: {', '.join(missing_columns)}。请确保文件包含 item_barcode 和 new_name 列"
            )

        # 只保留必需的列
        df = df[required_columns]

        # 删除空行
        df = df.dropna(subset=['item_barcode'])

        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()

        # 统计导入结果
        total = len(df)
        success = 0
        failed = 0
        updated = 0

        try:
            # 批量更新 new_name 字段
            for _, row in df.iterrows():
                try:
                    item_barcode = str(row['item_barcode']).strip()
                    new_name = str(row['new_name']).strip() if pd.notna(row['new_name']) else None

                    # 使用 UPDATE 仅更新 new_name 字段
                    sql = """
                        UPDATE barcode_base_info_69_top96_incre_allplatform_name
                        SET new_name = %s
                        WHERE item_barcode = %s
                    """
                    affected = cursor.execute(sql, (new_name, item_barcode))
                    if affected > 0:
                        updated += 1
                    success += 1
                except Exception as e:
                    failed += 1
                    print(f"更新失败: {item_barcode}, 错误: {e}")

            conn.commit()

        finally:
            cursor.close()
            conn.close()

        return {
            "success": True,
            "message": "数据导入完成",
            "total": total,
            "success": success,
            "updated": updated,
            "failed": failed
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")

@app.put("/api/update")
async def update_data(item_barcode: str, new_name: str):
    """
    更新 new_name 字段

    参数:
        item_barcode: 商品条码
        new_name: 新的商品名称
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 更 new_name 字段
        sql = """
            UPDATE barcode_base_info_69_top96_incre_allplatform_name
            SET new_name = %s
            WHERE item_barcode = %s
        """
        affected = cursor.execute(sql, (new_name, item_barcode))
        conn.commit()

        cursor.close()
        conn.close()

        if affected == 0:
            raise HTTPException(status_code=404, detail=f"未找到条码: {item_barcode}")

        return {
            "success": True,
            "message": "更新成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@app.get("/api/data")
async def get_data(page: int = 1, pageSize: int = 50, keyword: Optional[str] = None):
    """
    获取数据

    参数:
        page: 页码 (默认: 1)
        pageSize: 每页记录数 (默认: 50)
        keyword: 搜索关键词 (搜索 item_barcode, item_name, new_name, msy_item_name, eb_item_name, mt_item_name, gs1_item_name)
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 构建查询条件
        where_clause = ""
        params = []

        if keyword:
            where_clause = """ WHERE item_barcode LIKE %s
                                OR item_name LIKE %s
                                OR new_name LIKE %s
                                OR msy_item_name LIKE %s
                                OR eb_item_name LIKE %s
                                OR mt_item_name LIKE %s
                                OR gs1_item_name LIKE %s
                                OR old_cat_name LIKE %s
                                OR new_cat_name LIKE %s """
            like_pattern = f"%{keyword}%"
            params = [like_pattern] * 9

        # 获取总记录数
        count_sql = f"SELECT COUNT(*) as total FROM barcode_base_info_69_top96_incre_allplatform_name{where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()['total']

        # 获取分页数据
        offset = (page - 1) * pageSize
        data_sql = f"""SELECT item_barcode, item_name, old_cat_name, new_cat_name,
                          msy_item_name, msy_cat_name, eb_item_name, eb_cat_name, eb_size,
                          mt_item_name, mt_cat_name, mt_size, gs1_item_name, new_name, valid_flag
                   FROM barcode_base_info_69_top96_incre_allplatform_name
                   {where_clause}
                   ORDER BY item_barcode LIMIT %s OFFSET %s"""
        cursor.execute(data_sql, params + [pageSize, offset])
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "data": data,
            "total": total,
            "page": page,
            "pageSize": pageSize
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据失败: {str(e)}")

@app.get("/api/export")
async def export_data(format: str = "excel"):
    """
    导出数据

    参数:
        format: 导出格式 (excel 或 csv，默认: excel)
    """
    import re
    import traceback
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取所有数据
        cursor.execute(
            """SELECT item_barcode, item_name, old_cat_name, new_cat_name,
                      msy_item_name, msy_cat_name, eb_item_name, eb_cat_name, eb_size,
                      mt_item_name, mt_cat_name, mt_size, gs1_item_name, new_name, valid_flag
               FROM barcode_base_info_69_top96_incre_allplatform_name
               ORDER BY item_barcode"""
        )
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        print(f"[DEBUG] 导出数据条数: {len(data)}")

        # 创建 DataFrame 并清理非法字符（替换为空格）
        def clean_value(val):
            if val is None:
                return None
            if isinstance(val, str):
                # 将 Excel 不支持的非法字符替换为空格
                return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', ' ', val)
            return val

        # 清理数据
        cleaned_data = []
        for row in data:
            cleaned_row = {k: clean_value(v) for k, v in row.items()}
            cleaned_data.append(cleaned_row)

        df = pd.DataFrame(cleaned_data)

        if df.empty:
            raise HTTPException(status_code=404, detail="表中暂无数据")

        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = static_dir / "exports"
        export_dir.mkdir(exist_ok=True)

        print(f"[DEBUG] 导出目录: {export_dir}")

        if format.lower() == "csv":
            filename = f"barcode_data_export_{timestamp}.csv"
            filepath = export_dir / filename
            # CSV 不需要清理，导出原始数据
            df_raw = pd.DataFrame(data)
            df_raw.to_csv(str(filepath), index=False, encoding='utf-8-sig')
            media_type = 'text/csv; charset=utf-8'
        else:
            filename = f"barcode_data_export_{timestamp}.xlsx"
            filepath = export_dir / filename
            df.to_excel(str(filepath), index=False, engine='openpyxl')
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        print(f"[DEBUG] 文件生成成功: {filepath}")

        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] 导出异常: {str(e)}")
        print(f"[ERROR] 详细堆栈:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """获取统计信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as total FROM barcode_base_info_69_top96_incre_allplatform_name")
        total = cursor.fetchone()['total']

        # 获取最后更新时间（从表的结构中无法直接获取，使用当前时间）
        lastUpdate = datetime.now().isoformat()

        cursor.close()
        conn.close()

        return {
            "success": True,
            "total": total,
            "lastUpdate": lastUpdate
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

# ===== Data Tools API =====

@app.get("/api/tables")
async def get_tables():
    """获取数据库所有表"""
    try:
        print("[DEBUG] 正在获取表列表...")
        tables = sql_validator.get_tables()
        print(f"[DEBUG] 获取到 {len(tables)} 个表")
        return {
            "success": True,
            "tables": tables
        }
    except Exception as e:
        print(f"[ERROR] 获取表列表失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")

@app.get("/api/tables/{table}/columns")
async def get_table_columns(table: str):
    """获取指定表的字段信息"""
    try:
        # 验证表名
        if not sql_validator.validate_table_name(table):
            raise HTTPException(status_code=400, detail=f"无效的表名: {table}")

        columns = sql_validator.get_columns(table)

        # 格式化字段信息
        formatted_columns = []
        for col in columns:
            formatted_columns.append({
                "name": col['COLUMN_NAME'],
                "type": col['DATA_TYPE'],
                "nullable": col['IS_NULLABLE'] == 'YES',
                "comment": col.get('COLUMN_COMMENT', '')
            })

        return {
            "success": True,
            "table": table,
            "columns": formatted_columns
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取字段信息失败: {str(e)}")

@app.post("/api/query/preview")
async def preview_query(request: QueryRequest):
    """预览查询 - 返回 SQL、预估行数、前 10 条数据"""
    try:
        # 验证表名
        if not sql_validator.validate_table_name(request.table):
            raise HTTPException(status_code=400, detail=f"无效的表名: {request.table}")

        # 验证字段名
        if not sql_validator.validate_field_names(request.table, request.fields):
            raise HTTPException(status_code=400, detail="包含无效的字段名")

        # 验证 limit
        if not sql_validator.validate_limit(request.limit):
            raise HTTPException(status_code=400, detail="limit 必须在 1-100000 之间")

        # 转换条件格式
        conditions = None
        if request.conditions:
            conditions = [c.model_dump() for c in request.conditions]

        # 构建 COUNT SQL
        count_sql, count_params = query_builder.build_count(
            request.table, conditions
        )

        # 构建 SELECT SQL
        select_sql, select_params = query_builder.build_select(
            request.table, request.fields, conditions, limit=10
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 获取预估行数
            cursor.execute(count_sql, count_params)
            total = cursor.fetchone()['total']

            # 获取预览数据
            cursor.execute(select_sql, select_params)
            preview_data = cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

        return {
            "success": True,
            "sql": select_sql,
            "params": select_params,
            "estimatedRows": total,
            "preview": preview_data
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览查询失败: {str(e)}")

@app.post("/api/query/export")
async def export_query(request: QueryRequest, format: str = Query(default="excel")):
    """执行查询并导出"""
    try:
        # 验证表名
        if not sql_validator.validate_table_name(request.table):
            raise HTTPException(status_code=400, detail=f"无效的表名: {request.table}")

        # 验证字段名
        if not sql_validator.validate_field_names(request.table, request.fields):
            raise HTTPException(status_code=400, detail="包含无效的字段名")

        # JSON 格式返回（用于前端分批合并）
        if format.lower() == "json":
            # 转换条件格式
            conditions = None
            if request.conditions:
                conditions = [c.model_dump() for c in request.conditions]

            # 构建 SQL
            select_sql, select_params = query_builder.build_select(
                request.table, request.fields, conditions,
                limit=request.limit,
                offset=request.offset
            )

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(select_sql, select_params)
                data = cursor.fetchall()
            finally:
                cursor.close()
                conn.close()

            return {
                "success": True,
                "data": data,
                "count": len(data),
                "offset": request.offset or 0
            }

        # 验证导出 limit（文件导出模式）
        if not sql_validator.validate_export_limit(request.limit):
            raise HTTPException(status_code=400, detail="导出数量不能超过 100000 条")

        # 转换条件格式
        conditions = None
        if request.conditions:
            conditions = [c.model_dump() for c in request.conditions]

        # 构建 SQL
        select_sql, select_params = query_builder.build_select(
            request.table, request.fields, conditions, limit=request.limit
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(select_sql, select_params)
            data = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

        if not data:
            raise HTTPException(status_code=404, detail="没有符合条件的数据")

        # 创建 DataFrame
        import re
        df = pd.DataFrame(data)

        # 清理非法字符（用于 Excel 导出）
        def clean_value(val):
            if val is None:
                return None
            if isinstance(val, str):
                return re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', ' ', val)
            return val

        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = static_dir / "exports"
        export_dir.mkdir(exist_ok=True)

        if format.lower() == "csv":
            filename = f"query_export_{timestamp}.csv"
            filepath = export_dir / filename
            df.to_csv(str(filepath), index=False, encoding='utf-8-sig')
            media_type = 'text/csv; charset=utf-8'
        else:
            # Excel 需要清理非法字符
            cleaned_data = [{k: clean_value(v) for k, v in row.items()} for row in data]
            df_cleaned = pd.DataFrame(cleaned_data)
            filename = f"query_export_{timestamp}.xlsx"
            filepath = export_dir / filename
            df_cleaned.to_excel(str(filepath), index=False, engine='openpyxl')
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return FileResponse(
            path=str(filepath),
            filename=filename,
            media_type=media_type
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出查询失败: {str(e)}")

# ===== Batch Update API =====

@app.post("/api/query/update/preview")
async def preview_update(request: UpdateRequest):
    """预览 UPDATE 操作"""
    try:
        # 验证表名
        if not sql_validator.validate_table_name(request.table):
            raise HTTPException(status_code=400, detail=f"无效的表名: {request.table}")

        # 检查是否有要更新的字段
        if not request.field_values:
            raise HTTPException(status_code=400, detail="至少需要一个要更新的字段")

        # 验证字段名
        fields = list(request.field_values.keys())
        if not sql_validator.validate_field_names(request.table, fields):
            raise HTTPException(status_code=400, detail="包含无效的字段名")

        # 获取表的主键字段
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
        """, (db_config['database'], request.table))
        primary_keys = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        cursor.close()
        conn.close()

        # 检查是否尝试更新主键
        updating_pk = any(f in primary_keys for f in fields)
        if updating_pk:
            raise HTTPException(status_code=400, detail="禁止更新主键字段")

        # 安全检查：如果没有任何条件，需要确认
        has_conditions = request.conditions and len(request.conditions) > 0
        if not has_conditions and not request.force_no_where:
            raise HTTPException(
                status_code=400,
                detail="更新操作必须有 WHERE 条件，或者设置 force_no_where=true 确认更新所有数据"
            )

        # 转换条件格式
        conditions = None
        if request.conditions:
            conditions = [c.model_dump() for c in request.conditions]

        # 构建 COUNT SQL
        count_sql, count_params = query_builder.build_count(
            request.table, conditions
        )

        # 构建 UPDATE SQL
        update_sql, update_params = query_builder.build_update(
            request.table, request.field_values, conditions, request.limit
        )

        # 获取预估影响行数
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(count_sql, count_params)
            estimated_rows = cursor.fetchone()['total']
        finally:
            cursor.close()
            conn.close()

        # 获取预览数据（前 5 条）
        preview_data = []
        if estimated_rows > 0:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 构建预览查询
                preview_fields = list(request.field_values.keys())[:5]  # 最多显示 5 个字段
                select_sql, select_params = query_builder.build_select(
                    request.table, preview_fields, conditions, limit=5
                )

                cursor.execute(select_sql, select_params)
                preview_data = cursor.fetchall()
            finally:
                cursor.close()
                conn.close()

        return {
            "success": True,
            "updateSql": update_sql,
            "estimatedRows": estimated_rows,
            "preview": preview_data,
            "hasWhere": has_conditions,
            "updatingFields": list(request.field_values.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览更新失败: {str(e)}")

@app.post("/api/query/update/execute")
async def execute_update(request: UpdateRequest):
    """执行 UPDATE 操作"""
    try:
        # 验证表名
        if not sql_validator.validate_table_name(request.table):
            raise HTTPException(status_code=400, detail=f"无效的表名: {request.table}")

        # 检查是否有要更新的字段
        if not request.field_values:
            raise HTTPException(status_code=400, detail="至少需要一个要更新的字段")

        # 验证字段名
        fields = list(request.field_values.keys())
        if not sql_validator.validate_field_names(request.table, fields):
            raise HTTPException(status_code=400, detail="包含无效的字段名")

        # 获取表的主键字段
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
            AND TABLE_NAME = %s
            AND CONSTRAINT_NAME = 'PRIMARY'
        """, (db_config['database'], request.table))
        primary_keys = {row['COLUMN_NAME'] for row in cursor.fetchall()}
        cursor.close()

        # 检查是否尝试更新主键
        updating_pk = any(f in primary_keys for f in fields)
        if updating_pk:
            raise HTTPException(status_code=400, detail="禁止更新主键字段")

        # 安全检查
        has_conditions = request.conditions and len(request.conditions) > 0
        if not has_conditions and not request.force_no_where:
            raise HTTPException(
                status_code=400,
                detail="更新操作必须有 WHERE 条件"
            )

        # 限制更新行数
        if request.limit and request.limit > 10000:
            raise HTTPException(status_code=400, detail="单次更新不能超过 10000 条")

        # 转换条件格式
        conditions = None
        if request.conditions:
            conditions = [c.model_dump() for c in request.conditions]

        # 构建 UPDATE SQL
        update_sql, update_params = query_builder.build_update(
            request.table, request.field_values, conditions, request.limit
        )

        # 执行 UPDATE
        cursor = conn.cursor()
        try:
            affected_rows = cursor.execute(update_sql, update_params)
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return {
            "success": True,
            "affectedRows": affected_rows,
            "message": f"成功更新 {affected_rows} 条数据"
        }

    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"执行更新失败: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

# ===== Run Server =====
if __name__ == "__main__":
    import uvicorn

    print("=" * 50)
    print("内网数据导入导出系统")
    print("=" * 50)
    print(f"数据库: {db_config['database']}")
    print(f"目标表: barcode_base_info_69_top96_incre_allplatform_name")
    print(f"监听地址: http://0.0.0.0:11219")
    print("=" * 50)
    print("系统启动中...")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=11219,
        log_level="info"
    )
