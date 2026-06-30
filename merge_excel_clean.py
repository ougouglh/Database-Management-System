#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将源 Excel 中"人工清洗"列的数据通过 item_barcode 关联，更新到目标 Excel 的"人工清洗"列
"""
import pandas as pd
import argparse
import shutil
from pathlib import Path


def merge_clean_column(
    source_file: str,
    target_file: str,
    output_file: str = None,
    key_col: str = 'item_barcode',
    clean_col: str = '人工清洗'
):
    """
    通过 item_barcode 关联，将源文件中"人工清洗"列的数据合并到目标文件

    Args:
        source_file: 源文件（包含"人工清洗"数据）
        target_file: 目标文件（需要被更新）
        output_file: 输出文件（默认覆盖目标文件）
        key_col: 关联键
        clean_col: 人工清洗列名
    """
    if output_file is None:
        output_file = target_file

    print("=" * 60)
    print(f"源文件: {source_file}")
    print(f"目标文件: {target_file}")
    print(f"输出文件: {output_file}")
    print(f"关联键: {key_col}")
    print(f"合并列: {clean_col}")
    print("=" * 60)

    # 读取源文件和目标文件
    print("\n正在读取 Excel 文件...")
    df_source = pd.read_excel(source_file, engine='openpyxl')
    df_target = pd.read_excel(target_file, engine='openpyxl')

    print(f"源文件: {len(df_source)} 行")
    print(f"目标文件: {len(df_target)} 行")

    # 校验必需的列
    for col in [key_col, clean_col]:
        if col not in df_source.columns:
            raise ValueError(f"源文件缺少必需的列: {col}")
        if col not in df_target.columns:
            raise ValueError(f"目标文件缺少必需的列: {col}")

    # 检查关联键是否唯一
    if df_source[key_col].duplicated().any():
        dup_count = df_source[key_col].duplicated().sum()
        print(f"\n⚠️  源文件中 {key_col} 有 {dup_count} 个重复值，将使用最后一条记录")
        df_source = df_source.drop_duplicates(subset=[key_col], keep='last')

    # 统计源文件中的有效"人工清洗"数据
    source_clean = df_source[clean_col].dropna()
    source_clean_non_empty = source_clean[source_clean.astype(str).str.strip() != '']
    print(f"\n源文件'人工清洗'列有效数据: {len(source_clean_non_empty)} 条")

    # 创建源数据的映射字典
    clean_map = {}
    for _, row in df_source.iterrows():
        key = row[key_col]
        clean_val = row[clean_col]
        if pd.notna(clean_val) and str(clean_val).strip() != '':
            clean_map[key] = clean_val

    print(f"源文件中可关联的有效'人工清洗'数据: {len(clean_map)} 条")

    # 创建备份
    if output_file == target_file:
        backup_file = target_file.replace('.xlsx', '_backup.xlsx')
        shutil.copy2(target_file, backup_file)
        print(f"\n已创建备份: {backup_file}")

    # 更新目标文件的"人工清洗"列
    updated_count = 0
    new_value_count = 0
    update_value_count = 0
    no_match_count = 0
    no_change_count = 0

    for idx, row in df_target.iterrows():
        key = row[key_col]
        if key in clean_map:
            new_value = clean_map[key]
            old_value = row[clean_col]
            # 只有当新值与旧值不同时才更新
            if pd.isna(old_value) or str(old_value).strip() == '':
                new_value_count += 1
            else:
                if str(old_value).strip() != str(new_value).strip():
                    update_value_count += 1
                else:
                    no_change_count += 1
            df_target.at[idx, clean_col] = new_value
            updated_count += 1
        else:
            no_match_count += 1

    # 统计
    print("\n" + "=" * 60)
    print("更新统计")
    print("=" * 60)
    print(f"目标文件总行数: {len(df_target)}")
    print(f"通过 {key_col} 匹配到的行数: {updated_count}")
    print(f"  - 新增'人工清洗'值: {new_value_count} 条")
    print(f"  - 更新已存在的'人工清洗'值: {update_value_count} 条")
    print(f"  - 值未发生变化: {no_change_count} 条")
    print(f"未匹配到源数据的行数: {no_match_count}")

    # 检查源文件中有但目标文件中没有的 barcode
    target_keys = set(df_target[key_col].dropna().tolist())
    source_keys = set(df_source[key_col].dropna().tolist())
    missing_in_target = source_keys - target_keys
    print(f"\n源文件有但目标文件没有的 barcode: {len(missing_in_target)} 个")
    if missing_in_target and len(missing_in_target) <= 10:
        print(f"  示例: {list(missing_in_target)[:10]}")
    elif missing_in_target:
        print(f"  示例: {list(missing_in_target)[:10]} ...")

    # 保存到新文件
    print(f"\n正在保存到: {output_file}")
    df_target.to_excel(output_file, index=False, engine='openpyxl')

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='Excel 人工清洗列合并工具')
    parser.add_argument('source_file', help='源 Excel 文件（包含人工清洗数据）')
    parser.add_argument('target_file', help='目标 Excel 文件（需要被更新）')
    parser.add_argument('--output', '-o', help='输出文件路径（默认覆盖目标文件）')
    parser.add_argument('--key', default='item_barcode', help='关联键字段名（默认 item_barcode）')
    parser.add_argument('--column', default='人工清洗', help='要合并的列名（默认 人工清洗）')

    args = parser.parse_args()

    if not Path(args.source_file).exists():
        print(f"错误: 源文件不存在: {args.source_file}")
        return 1

    if not Path(args.target_file).exists():
        print(f"错误: 目标文件不存在: {args.target_file}")
        return 1

    try:
        merge_clean_column(
            source_file=args.source_file,
            target_file=args.target_file,
            output_file=args.output,
            key_col=args.key,
            clean_col=args.column
        )
        return 0
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
