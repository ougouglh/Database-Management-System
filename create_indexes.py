#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建索引脚本
"""

import yaml
import pymysql

def create_index():
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    db_config = config['mysql1']

    conn = pymysql.connect(
        host=db_config['host'],
        port=db_config['port'],
        user=db_config['user'],
        password=db_config['password'],
        database=db_config['database'],
        charset=db_config['charset']
    )

    tables = [
        'barcode_base_info_69_top96_incre_allplatform_name',
        'barcode_base_info_top96_incre_msy_20260515',
        'test_pps_item_msy38000_20260519'
    ]

    try:
        with conn.cursor() as cursor:
            for table in tables:
                print(f"\n检查表: {table}")

                cursor.execute(f"SHOW INDEX FROM {table}")
                indexes = cursor.fetchall()

                barcodes = [idx for idx in indexes if idx[4] == 'item_barcode']
                if barcodes:
                    print(f"  item_barcode 已有索引: {[idx[2] for idx in barcodes]}")
                else:
                    print(f"  item_barcode 无索引，正在创建...")
                    cursor.execute(f"CREATE INDEX idx_item_barcode ON {table}(item_barcode)")
                    conn.commit()
                    print(f"  创建成功!")

    finally:
        conn.close()

    print("\n完成!")

if __name__ == '__main__':
    create_index()
