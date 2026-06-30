#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV 导入工具：将 CSV 文件导入到 MySQL 数据库
支持数据校验功能
"""

import yaml
import pymysql
import csv
import argparse
import time
from tqdm import tqdm
from data_validator import DataValidator, validate_csv


class Config:
    """配置类"""

    def __init__(self, config_file: str = "config.yaml"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 使用 mysql1 配置 (bigdata_main_data2)
        self.target = config['mysql1']

    def get_connection(self) -> pymysql.Connection:
        """获取数据库连接"""
        return pymysql.connect(
            host=self.target['host'],
            port=self.target['port'],
            user=self.target['user'],
            password=self.target['password'],
            database=self.target['database'],
            charset=self.target['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )


def get_batch_size(total_count: int) -> int:
    """根据总量自适应计算批次大小"""
    if total_count < 10_000:
        return 1_000
    elif total_count < 100_000:
        return 5_000
    else:
        return 10_000


def create_table_if_not_exists(conn: pymysql.Connection, sql_file: str):
    """如果表不存在则创建"""
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql = f.read()

    # 提取表名
    table_name = sql.split('CREATE TABLE `')[1].split('`')[0]

    # 检查表是否存在
    with conn.cursor() as cursor:
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if cursor.fetchone():
            print(f"表 {table_name} 已存在，跳过创建")
            return table_name

    # 表不存在，创建表
    print(f"\n正在创建表: {table_name}")
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            conn.commit()
            print(f"表 {table_name} 创建成功")
            return table_name
    except Exception as e:
        print(f"建表失败: {e}")
        raise


def count_csv_rows(csv_file: str) -> int:
    """统计 CSV 文件行数"""
    with open(csv_file, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f) - 1  # 减去表头


def import_csv(conn: pymysql.Connection, csv_file: str, table_name: str):
    """导入 CSV 数据"""

    # 1. 统计 CSV 行数
    print(f"\n正在统计 CSV 文件行数...")
    total_rows = count_csv_rows(csv_file)
    print(f"CSV 文件共有 {total_rows:,} 条记录（不含表头）")

    if total_rows == 0:
        print("没有数据需要导入")
        return

    # 2. 自适应批次大小
    batch_size = get_batch_size(total_rows)
    print(f"批次大小: {batch_size:,} 条/批")

    # 3. 开始导入
    print("\n开始导入...")

    successful = 0
    failed = 0
    start_time = time.time()

    with tqdm(
        total=total_rows,
        desc="导入数据",
        unit="条",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}, ETA: {remaining}]"
    ) as pbar:

        batch = []
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # 跳过包含"无此条码"的无效行
                    row_values = [str(v) for v in row.values() if v]
                    if any('无此条码' in val for val in row_values):
                        failed += 1
                        continue

                    # 处理数据
                    item_barcode = row['item_barcode'].strip()
                    item_name = row['item_name'].strip() if row['item_name'] else None
                    product_name = row['product_name'].strip() if row['product_name'] else None
                    brand = row['brand'].strip() if row['brand'] else None
                    group = row['group'].strip() if row['group'] else None
                    manufacturer = row['manufacturer'].strip() if row['manufacturer'] else None
                    category = row['category'].strip() if row['category'] else None

                    # 处理 median_price
                    median_price_str = row['median_price'].strip() if row['median_price'] else None
                    median_price = None
                    if median_price_str and median_price_str not in ['无法识别', '', 'N/A', 'NULL', 'None', '无此条码']:
                        try:
                            median_price = float(median_price_str)
                        except (ValueError, TypeError):
                            median_price = None

                    # 处理 first_order_date
                    first_order_date = row['first_order_date'].strip() if row['first_order_date'] else None
                    # 过滤无效日期
                    if first_order_date and first_order_date in ['无法识别', '', 'N/A', 'NULL', 'None']:
                        first_order_date = None
                    elif first_order_date and len(first_order_date) < 10:
                        # 补全日期格式 (如 2024-1-1 -> 2024-01-01)
                        parts = first_order_date.split('-')
                        if len(parts) == 3:
                            year, month, day = parts
                            first_order_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

                    screenshot_path = row['screenshot_path'].strip() if row['screenshot_path'] else None

                    batch.append((
                        item_barcode, item_name, product_name, brand, group,
                        manufacturer, category, median_price, first_order_date, screenshot_path
                    ))

                    # 批量插入
                    if len(batch) >= batch_size:
                        with conn.cursor() as cursor:
                            cursor.executemany(
                                f"""INSERT INTO {table_name} (
                                    item_barcode, item_name, product_name, brand, `group`,
                                    manufacturer, category, median_price, first_order_date, screenshot_path
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ON DUPLICATE KEY UPDATE
                                    item_name = VALUES(item_name),
                                    product_name = VALUES(product_name),
                                    brand = VALUES(brand),
                                    `group` = VALUES(`group`),
                                    manufacturer = VALUES(manufacturer),
                                    category = VALUES(category),
                                    median_price = VALUES(median_price),
                                    first_order_date = VALUES(first_order_date),
                                    screenshot_path = VALUES(screenshot_path)""",
                                batch
                            )
                            conn.commit()

                        successful += len(batch)
                        pbar.update(len(batch))
                        batch = []

                except Exception as e:
                    failed += 1
                    pbar.write(f"\n行处理失败 (item_barcode: {row.get('item_barcode', 'N/A')}): {e}")

            # 插入剩余数据
            if batch:
                with conn.cursor() as cursor:
                    cursor.executemany(
                        f"""INSERT INTO {table_name} (
                            item_barcode, item_name, product_name, brand, `group`,
                            manufacturer, category, median_price, first_order_date, screenshot_path
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            item_name = VALUES(item_name),
                            product_name = VALUES(product_name),
                            brand = VALUES(brand),
                            `group` = VALUES(`group`),
                            manufacturer = VALUES(manufacturer),
                            category = VALUES(category),
                            median_price = VALUES(median_price),
                            first_order_date = VALUES(first_order_date),
                            screenshot_path = VALUES(screenshot_path)""",
                        batch
                    )
                    conn.commit()

                successful += len(batch)
                pbar.update(len(batch))

    # 4. 统计结果
    elapsed = time.time() - start_time

    print("\n" + "=" * 50)
    print("导入完成！")
    print("=" * 50)
    print(f"成功: {successful:,} 条")
    print(f"失败: {failed:,} 条")
    print(f"耗时: {elapsed:.2f} 秒")
    print(f"速度: {successful / elapsed:,.0f} 条/秒")
    print("=" * 50)


def verify_data(conn: pymysql.Connection, table_name: str, csv_file: str):
    """验证导入数据"""

    print("\n正在验证数据...")

    # 统计 CSV 行数
    csv_rows = count_csv_rows(csv_file)

    # 统计表记录数
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) as total FROM {table_name}")
        table_rows = cursor.fetchone()['total']

    print(f"CSV 记录: {csv_rows:,}")
    print(f"表记录: {table_rows:,}")

    if csv_rows == table_rows:
        print("记录数一致!")
    else:
        print(f"警告: 记录数不一致! 相差 {abs(csv_rows - table_rows):,}")


def main():
    """主函数"""

    parser = argparse.ArgumentParser(description='CSV 导入工具')
    parser.add_argument('csv_file', help='CSV 文件路径')
    parser.add_argument('--sql', default='create_table.sql', help='建表 SQL 文件')
    parser.add_argument('--validate', action='store_true', help='导入前进行数据校验')
    parser.add_argument('--strict', action='store_true', help='严格模式：有警告也拒绝导入')
    args = parser.parse_args()

    print("=" * 50)
    print("CSV 导入工具")
    print(f"CSV 文件: {args.csv_file}")
    print(f"SQL 文件: {args.sql}")
    print(f"目标数据库: bigdata_main_data2")
    print("=" * 50)

    # 数据校验
    if args.validate:
        print("\n正在进行数据校验...")
        validator = DataValidator(strict_mode=args.strict)
        errors, warnings, infos, results = validator.validate_file(args.csv_file)
        validator.print_summary(args.csv_file)

        if errors > 0:
            print("\n❌ 数据校验失败，存在错误，导入已取消")
            return

        if warnings > 0 and args.strict:
            print("\n❌ 数据校验失败，存在警告（严格模式），导入已取消")
            return

        print("\n是否继续导入？", end=" ")
        if args.strict:
            print("(按 Enter 继续，按 Ctrl+C 取消)")
        else:
            confirm = input("(按 Enter 继续，按 Ctrl+C 取消)")

    # 加载配置
    try:
        config = Config()
    except Exception as e:
        print(f"配置文件加载失败: {e}")
        return

    # 连接数据库
    try:
        conn = config.get_connection()
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return

    try:
        # 创建表（如果不存在）
        table_name = create_table_if_not_exists(conn, args.sql)

        # 导入数据
        import_csv(conn, args.csv_file, table_name)

        # 验证数据
        verify_data(conn, table_name, args.csv_file)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
