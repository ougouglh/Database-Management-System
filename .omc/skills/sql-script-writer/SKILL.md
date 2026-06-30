---
name: sql-script-writer
description: 为 MySQL 项目撰写数据迁移、CSV 导入/导出等数据库操作脚本。当用户需要迁移数据、导入 CSV 文件到数据库、表之间复制数据、批量处理数据库记录时使用此技能。遵循项目既定风格：Config 类封装、自适应批次、tqdm 进度条、完善错误处理。使用此技能前必须先了解操作类型、源/目标信息、表结构和数据量级。
tags: sql, database, script, migration, import, export, csv, mysql, batch
---

# SQL 脚本撰写规范

此技能用于为 MySQL 项目撰写数据操作脚本，遵循项目既定的代码风格和最佳实践。

## 撰写前必须收集的信息

在编写脚本之前，**必须**先询问用户以下信息：

1. **操作类型**：数据迁移 / CSV 导入 / CSV 导出 / 其他？
2. **源信息**：
   - 如果是迁移：源数据库、源表名
   - 如果是导入：CSV 文件路径
3. **目标信息**：目标数据库、目标表名
4. **表结构**：有哪些字段？每个字段的数据类型是什么？
5. **数据量级**：大概有多少条数据？（影响批次大小设置）
6. **特殊处理**：
   - 是否需要去重？（主键/唯一键冲突如何处理）
   - 是否需要数据转换？（日期格式、编码等）
   - 是否需要断点续传？

## 项目代码风格规范

### 1. 文件结构

```
project/
├── config.yaml           # 数据库配置（复用现有）
├── script_name.py        # 主脚本
└── create_table.sql      # 建表 SQL（如需创建表）
```

### 2. Config 类封装

所有数据库配置和连接管理通过 Config 类封装：

```python
class Config:
    def __init__(self, config_file: str = "config.yaml"):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        self.source = config['mysql2']   # 或其他源
        self.target = config['mysql1']   # 或其他目标

    def get_connection(self, db_type: str = 'source') -> pymysql.Connection:
        cfg = self.source if db_type == 'source' else self.target
        return pymysql.connect(
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            database=cfg['database'],
            charset=cfg['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )
```

### 3. 自适应批次大小

根据数据总量自动调整批次大小，平衡内存使用和性能：

```python
def get_batch_size(total_count: int) -> int:
    if total_count < 10_000:
        return 1_000      # 小数据集：小批次
    elif total_count < 100_000:
        return 5_000      # 中等数据集
    else:
        return 10_000     # 大数据集：大批次
```

### 4. tqdm 进度条

使用 tqdm 显示实时进度，格式统一：

```python
from tqdm import tqdm

with tqdm(
    total=total_count,
    desc="操作描述",
    unit="条",
    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{rate_fmt}, ETA: {remaining}]"
) as pbar:
    # 处理数据
    pbar.update(count)
```

进度条显示示例：
```
复制数据: [██████████░░░░░░░░░░] 45% (4,500/10,000) | 1,250条/秒 | ETA: 00:00:04
```

### 5. 批量插入

使用 `executemany` 进行批量插入，不要逐条插入：

```python
# 收集一批数据
batch = [(value1, value2), (value1, value2), ...]

# 批量插入
cursor.executemany(
    "INSERT INTO table (col1, col2) VALUES (%s, %s)",
    batch
)
conn.commit()
```

### 6. 统计输出

操作完成后，统一使用以下格式输出统计信息：

```
==================================
操作完成！
==================================
成功: 10,000 条
失败: 0 条
耗时: 5.23 秒
速度: 1,912 条/秒
==================================
```

### 7. 错误处理

- 使用 try-except 捕获数据库连接和查询错误
- 批次失败时回滚并记录，不要中断整个流程
- 提供清晰的错误信息

### 8. 数据验证

操作完成后自动验证数据一致性：

```python
def verify_data(source_conn, target_conn, table):
    # 对比源表和目标表记录数
    # 输出验证结果
```

## 命令行参数

脚本应支持 argparse 命令行参数：

```python
import argparse

parser = argparse.ArgumentParser(description='脚本描述')
parser.add_argument('table', help='表名')
parser.add_argument('--batch-size', type=int, help='批次大小')
args = parser.parse_args()
```

## 依赖

标准依赖清单：

```
pymysql==1.1.0
tqdm==4.66.1
pyyaml==6.0.1
```

## SQL 建表规范

- 使用 `utf8mb4` 字符集
- 添加 COMMENT 注释
- 主键使用 `item_barcode`（条码字段）
- 日期字段根据精度选择 `date` 或 `datetime`

示例：
```sql
CREATE TABLE `table_name` (
  `item_barcode` varchar(50) NOT NULL COMMENT '商品条码',
  `item_name` varchar(255) DEFAULT NULL COMMENT '商品名称',
  PRIMARY KEY (`item_barcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表注释';
```

## 主键冲突处理

根据需求选择策略：

- `INSERT IGNORE` - 跳过重复数据
- `REPLACE INTO` - 覆盖重复数据
- `ON DUPLICATE KEY UPDATE` - 更新指定字段

示例：
```sql
INSERT INTO table (col1, col2) VALUES (%s, %s)
ON DUPLICATE KEY UPDATE col2 = VALUES(col2)
```
