#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据校验模块
"""

import csv
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    ERROR = "错误"      # 严重问题，会导致导入失败
    WARNING = "警告"   # 轻微问题，但可以导入
    INFO = "提示"      # 信息提示


@dataclass
class ValidationResult:
    level: ValidationLevel
    field: str
    row: int
    value: str
    message: str


class BarcodeValidator:
    """条码校验器"""

    KNOWN_FORMATS = {
        8: ["EAN-8", "UPC-A"],
        12: ["UPC-A", "Code 12"],
        13: ["EAN-13"],
        14: ["EAN-14", "ITF-14"]
    }

    @staticmethod
    def is_valid_length(barcode: str, min_len: int = 8, max_len: int = 14) -> bool:
        return min_len <= len(barcode) <= max_len

    @staticmethod
    def is_numeric(barcode: str) -> bool:
        return barcode.isdigit()

    @staticmethod
    def is_alphanumeric(barcode: str) -> bool:
        return barcode.isalnum()

    @staticmethod
    def validate_ean13(barcode: str) -> bool:
        if len(barcode) != 13 or not barcode.isdigit():
            return False

        digits = [int(d) for d in barcode]
        odd_sum = sum(digits[0::2])
        even_sum = sum(digits[1::2])
        check_digit = (10 - (odd_sum + 3 * even_sum) % 10) % 10

        return check_digit == digits[12]

    @staticmethod
    def validate(barcode: str) -> List[ValidationResult]:
        results = []
        barcode = barcode.strip()

        if not barcode:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                field="item_barcode",
                row=0,
                value=barcode,
                message="条码不能为空"
            ))
            return results

        if not BarcodeValidator.is_valid_length(barcode):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                field="item_barcode",
                row=0,
                value=barcode,
                message=f"条码长度异常（{len(barcode)}位），期望8-14位"
            ))

        if not BarcodeValidator.is_alphanumeric(barcode):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                field="item_barcode",
                row=0,
                value=barcode,
                message="条码包含特殊字符"
            ))

        if len(barcode) == 13 and barcode.isdigit():
            if not BarcodeValidator.validate_ean13(barcode):
                results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    field="item_barcode",
                    row=0,
                    value=barcode,
                    message="EAN-13校验位不正确"
                ))

        return results


class ItemNameValidator:
    """商品名称校验器"""

    MAX_LENGTH = 255
    MIN_LENGTH = 1

    NAN_VALUES = ['nan', 'null', 'none', 'undefined', '']

    @staticmethod
    def is_nan(value: str) -> bool:
        if value is None:
            return True
        value_lower = str(value).strip().lower()
        return value_lower in ItemNameValidator.NAN_VALUES

    @staticmethod
    def validate(item_name: str) -> List[ValidationResult]:
        results = []
        item_name = item_name.strip() if item_name else ""

        if ItemNameValidator.is_nan(item_name):
            results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                field="item_name",
                row=0,
                value=item_name,
                message="商品名称为空或无效值"
            ))
            return results

        if len(item_name) > ItemNameValidator.MAX_LENGTH:
            results.append(ValidationResult(
                level=ValidationLevel.ERROR,
                field="item_name",
                row=0,
                value=item_name[:50] + "...",
                message=f"商品名称过长（{len(item_name)}字符），最大{ItemNameValidator.MAX_LENGTH}字符"
            ))

        return results


class DataValidator:
    """数据校验主类"""

    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.barcode_validator = BarcodeValidator()
        self.item_name_validator = ItemNameValidator()
        self.results: List[ValidationResult] = []

    def validate_row(self, row: Dict[str, str], row_num: int) -> List[ValidationResult]:
        results = []

        barcode = row.get('item_barcode', row.get('barcode', ''))
        item_name = row.get('item_name', '')

        barcode_results = self.barcode_validator.validate(barcode)
        for r in barcode_results:
            r.row = row_num
            results.append(r)

        item_name_results = self.item_name_validator.validate(item_name)
        for r in item_name_results:
            r.row = row_num
            results.append(r)

        return results

    def validate_file(self, csv_file: str) -> Tuple[int, int, int, List[ValidationResult]]:
        errors = 0
        warnings = 0
        infos = 0
        all_results = []

        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, start=2):
                results = self.validate_row(row, row_num)
                for r in results:
                    if r.level == ValidationLevel.ERROR:
                        errors += 1
                    elif r.level == ValidationLevel.WARNING:
                        warnings += 1
                    else:
                        infos += 1
                    all_results.append(r)

        self.results = all_results
        return errors, warnings, infos, all_results

    def validate_dataframe(self, df) -> Tuple[int, int, int, List[ValidationResult]]:
        errors = 0
        warnings = 0
        infos = 0
        all_results = []

        barcode_col = 'item_barcode' if 'item_barcode' in df.columns else 'barcode'
        item_name_col = 'item_name'

        for row_num, (_, row) in enumerate(df.iterrows(), start=2):
            row_dict = {
                'item_barcode': str(row.get(barcode_col, '')),
                'item_name': str(row.get(item_name_col, ''))
            }
            results = self.validate_row(row_dict, row_num)
            for r in results:
                if r.level == ValidationLevel.ERROR:
                    errors += 1
                elif r.level == ValidationLevel.WARNING:
                    warnings += 1
                else:
                    infos += 1
                all_results.append(r)

        self.results = all_results
        return errors, warnings, infos, all_results

    def print_summary(self, file_name: str):
        print("\n" + "=" * 60)
        print(f"数据校验报告: {file_name}")
        print("=" * 60)

        errors = sum(1 for r in self.results if r.level == ValidationLevel.ERROR)
        warnings = sum(1 for r in self.results if r.level == ValidationLevel.WARNING)
        infos = sum(1 for r in self.results if r.level == ValidationLevel.INFO)

        print(f"\n校验结果统计:")
        print(f"  错误: {errors} 条")
        print(f"  警告: {warnings} 条")
        print(f"  提示: {infos} 条")

        if errors > 0:
            print(f"\n⚠️  存在 {errors} 个错误，数据导入将被拒绝")
        elif warnings > 0:
            print(f"\n⚡ 存在 {warnings} 个警告，数据可以导入但建议检查")
        else:
            print(f"\n✅ 数据校验通过")

        if self.results and len(self.results) <= 20:
            print("\n" + "-" * 60)
            print("详细结果:")
            for r in self.results:
                icon = "❌" if r.level == ValidationLevel.ERROR else "⚠️" if r.level == ValidationLevel.WARNING else "ℹ️"
                print(f"  {icon} [{r.level.value}] 行{r.row}: {r.field} = '{r.value[:30]}...' - {r.message}" if len(r.value) > 30 else f"  {icon} [{r.level.value}] 行{r.row}: {r.field} = '{r.value}' - {r.message}")
        elif self.results:
            print("\n" + "-" * 60)
            print("前10条问题:")
            for r in self.results[:10]:
                icon = "❌" if r.level == ValidationLevel.ERROR else "⚠️" if r.level == ValidationLevel.WARNING else "ℹ️"
                print(f"  {icon} [{r.level.value}] 行{r.row}: {r.field} = '{r.value[:30]}' - {r.message}")

        print("=" * 60)

        return errors == 0


def validate_csv(csv_file: str, strict_mode: bool = False) -> bool:
    validator = DataValidator(strict_mode=strict_mode)
    errors, warnings, infos, results = validator.validate_file(csv_file)
    validator.print_summary(csv_file)
    return errors == 0


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法: python data_validator.py <csv_file>")
        sys.exit(1)

    csv_file = sys.argv[1]
    validate_csv(csv_file)
