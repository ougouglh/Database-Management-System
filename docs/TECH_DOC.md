# 商品条码数据管理系统 - 技术文档

## 1. 项目概述

### 1.1 项目名称
内网数据导入导出系统（商品条码数据管理系统）

### 1.2 项目简介
本系统是一个用于管理和维护 `barcode_base_info_69_top96_incre_allplatform_name` 表数据的 Web 应用，支持数据的导入、导出、查询、编辑等功能。

### 1.3 业务背景
- 系统用于管理 69 开头 TOP96 增量商品条码信息
- 数据来源于多个平台（MSY、EB、MT、GS1）的汇总
- 需要定期导入新数据并维护商品名称、分类等字段
- 原有 MySQL 服务器存储空间不足，计划迁移至 StarRocks

---

## 2. 需求背景

### 2.1 业务痛点
1. **存储空间不足** - 原 MySQL 服务器容量达到上限
2. **数据分散** - 商品信息来源于多个平台，需要统一管理
3. **手工维护效率低** - 缺乏便捷的批量导入和编辑工具
4. **缺乏审核机制** - 数据导入后直接生效，无审核流程

### 2.2 业务需求
| 需求 | 优先级 | 说明 |
|------|--------|------|
| 数据导入导出 | P0 | 支持 Excel/CSV 格式 |
| 数据查询编辑 | P0 | 支持分页、搜索、在线编辑 |
| 存储迁移 | P0 | 从 MySQL 迁移至 StarRocks |
| 数据审核 | P1 | 导入数据需审核后生效 |
| 变更历史 | P1 | 记录数据变更痕迹 |
| 批量操作 | P2 | 批量删除、批量修改 |
| 数据看板 | P2 | 统计分析和质量报告 |

---

## 3. 技术架构

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户浏览器                              │
│                    (HTML/CSS/JavaScript)                      │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                       FastAPI 后端                            │
│  ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│  │  导入模块    │   导出模块   │   查询模块   │   编辑模块   │  │
│  └─────────────┴─────────────┴─────────────┴─────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │ PyMySQL / MySQL Client
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    StarRocks 数据库                           │
│  ┌─────────────────┬─────────────────┬─────────────────────┐ │
│  │    主业务表      │    中间过程表    │    历史记录表        │ │
│  │  barcode_base   │  pending_review │  change_log         │ │
│  └─────────────────┴─────────────────┴─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端 | HTML5 | - | 页面结构 |
| 前端 | CSS3 | - | 样式，使用 CSS 变量设计系统 |
| 前端 | JavaScript (ES6+) | - | 原生 JS，无框架依赖 |
| 后端 | Python | 3.x | 开发语言 |
| 后端 | FastAPI | 0.x | Web 框架 |
| 后端 | PyMySQL | 1.x | 数据库驱动 |
| 后端 | Pandas | 2.x | 数据处理 |
| 后端 | Uvicorn | 0.x | ASGI 服务器 |
| 数据库 | StarRocks | 3.x | 分析型数据库 |

### 3.3 目录结构

```
mysql/
├── app.py                      # FastAPI 主应用
├── import_csv.py               # CSV 批量导入工具
├── config.yaml                 # 配置文件
├── create_table.sql            # 建表 SQL
├── static/                     # 静态资源
│   ├── index.html             # 前端页面
│   ├── script.js              # 前端脚本
│   ├── styles.css             # 样式文件
│   └── exports/               # 导出文件目录
├── docs/                       # 文档目录
│   └── TECH_DOC.md            # 本文档
└── name/                       # 其他脚本目录
```

---

## 4. 功能模块

### 4.1 已实现功能

#### 4.1.1 数据导入
- 支持 Excel (.xlsx, .xls) 和 CSV 格式
- 文件要求：必须包含 `item_barcode` 和 `new_name` 列
- 导入逻辑：仅更新 `new_name` 字段，其他字段保持不变
- 支持拖拽上传
- 实时反馈导入进度和结果

#### 4.1.2 数据导出
- 导出格式：Excel (.xlsx) 或 CSV
- 导出内容：全量表数据
- 自动处理特殊字符
- 文件命名：带时间戳

#### 4.1.3 数据查询
- 分页展示：默认 50 条/页
- 关键词搜索：支持 9 个字段模糊匹配
  - item_barcode, item_name, new_name, msy_item_name
  - eb_item_name, mt_item_name, gs1_item_name
  - old_cat_name, new_cat_name
- 实时统计：总记录数、最后更新时间

#### 4.1.4 在线编辑
- 点击 `new_name` 字段弹出编辑框
- 单条记录修改
- 即时保存生效

### 4.2 待开发功能

#### 4.2.1 数据审核流程
```
┌─────────┐     ┌─────────────┐     ┌─────────┐
│ 上传文件 │ ──> │ 待审核表     │ ──> │ 审核通过 │ ──> 主表
└─────────┘     │ pending_    │     │         │
                │ review       │ ──> │ 审核拒绝 │ ──> 驳回
                └─────────────┘     └─────────┘
```

#### 4.2.2 变更历史记录
- 记录字段：操作人、操作时间、变更前后值
- 支持按条码查询历史
- 支持按时间范围查询

#### 4.2.3 批量操作
- 批量删除
- 批量修改分类
- 批量设置 valid_flag

#### 4.2.4 数据质量看板
- 总记录数统计
- 字段缺失率分析
- 重复条码检测
- 分类分布统计

---

## 5. 数据库设计

### 5.1 主业务表

```sql
CREATE TABLE `barcode_base_info_69_top96_incre_allplatform_name` (
  `item_barcode` VARCHAR(50) NOT NULL COMMENT '商品条码',
  `item_name` VARCHAR(255) COMMENT '商品名称',
  `old_cat_name` VARCHAR(255) COMMENT '旧分类名称',
  `new_cat_name` VARCHAR(255) COMMENT '新分类名称',
  `msy_item_name` VARCHAR(255) COMMENT 'MSY商品名称',
  `msy_cat_name` VARCHAR(255) COMMENT 'MSY分类名称',
  `eb_item_name` VARCHAR(255) COMMENT 'EB商品名称',
  `eb_cat_name` VARCHAR(255) COMMENT 'EB分类名称',
  `eb_size` VARCHAR(100) COMMENT 'EB规格',
  `mt_item_name` VARCHAR(255) COMMENT 'MT商品名称',
  `mt_cat_name` VARCHAR(255) COMMENT 'MT分类名称',
  `mt_size` VARCHAR(100) COMMENT 'MT规格',
  `gs1_item_name` VARCHAR(255) COMMENT 'GS1商品名称',
  `new_name` VARCHAR(255) COMMENT '新商品名称（人工维护）',
  `valid_flag` INT COMMENT '有效标志'
) ENGINE=OLAP
PROPERTIES (
  "replication_num" = "1"
);
```

### 5.2 中间过程表（待开发）

```sql
-- 待审核表
CREATE TABLE `barcode_pending_review` (
  `id` BIGINT NOT NULL COMMENT '主键',
  `item_barcode` VARCHAR(50) NOT NULL COMMENT '商品条码',
  `change_data` JSON COMMENT '变更内容',
  `submitter` VARCHAR(50) COMMENT '提交人',
  `status` VARCHAR(20) COMMENT '状态：pending/approved/rejected',
  `reviewer` VARCHAR(50) COMMENT '审核人',
  `review_time` DATETIME COMMENT '审核时间',
  `comment` VARCHAR(500) COMMENT '审核意见'
) PRIMARY KEY (`id`);

-- 变更记录表
CREATE TABLE `barcode_change_log` (
  `id` BIGINT NOT NULL COMMENT '主键',
  `item_barcode` VARCHAR(50) NOT NULL COMMENT '商品条码',
  `field_name` VARCHAR(50) COMMENT '字段名',
  `old_value` VARCHAR(255) COMMENT '旧值',
  `new_value` VARCHAR(255) COMMENT '新值',
  `operator` VARCHAR(50) COMMENT '操作人',
  `change_time` DATETIME COMMENT '变更时间'
) PRIMARY KEY (`id`);

-- 导入任务表
CREATE TABLE `import_task_log` (
  `task_id` BIGINT NOT NULL COMMENT '任务ID',
  `file_name` VARCHAR(255) COMMENT '文件名',
  `total_rows` INT COMMENT '总行数',
  `success_rows` INT COMMENT '成功行数',
  `failed_rows` INT COMMENT '失败行数',
  `status` VARCHAR(20) COMMENT '状态',
  `created_at` DATETIME COMMENT '创建时间',
  `created_by` VARCHAR(50) COMMENT '创建人'
) PRIMARY KEY (`task_id`);
```

---

## 6. API 接口文档

### 6.1 已实现接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 主页 |
| GET | `/api/health` | 健康检查 |
| POST | `/api/import` | 数据导入 |
| PUT | `/api/update` | 更新 new_name |
| GET | `/api/data` | 获取数据（分页、搜索） |
| GET | `/api/export` | 导出数据 |
| GET | `/api/stats` | 统计信息 |

### 6.2 待开发接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/review/submit` | 提交审核 |
| POST | `/api/review/approve` | 审核通过 |
| POST | `/api/review/reject` | 审核拒绝 |
| GET | `/api/review/list` | 待审核列表 |
| GET | `/api/history/:barcode` | 变更历史 |
| POST | `/api/batch/delete` | 批量删除 |
| POST | `/api/batch/update` | 批量更新 |
| GET | `/api/dashboard` | 数据看板 |

---

## 7. 开发任务清单

### 7.1 StarRocks 迁移（P0）

- [ ] 获取 StarRocks 服务器连接信息
- [ ] 修改 `config.yaml` 添加 StarRocks 配置
- [ ] 转换建表 SQL 适配 StarRocks 语法
- [ ] 测试数据库连接
- [ ] 验证 API 功能正常

### 7.2 数据审核功能（P1）

- [ ] 创建待审核表
- [ ] 修改导入流程：数据先进入待审核表
- [ ] 开发审核页面
- [ ] 实现审核通过/拒绝接口
- [ ] 添加待审核列表接口

### 7.3 变更历史功能（P1）

- [ ] 创建变更记录表
- [ ] 在数据更新时自动记录变更
- [ ] 开发历史查看页面
- [ ] 实现历史查询接口

### 7.4 批量操作（P2）

- [ ] 表格增加复选框
- [ ] 实现批量删除接口
- [ ] 实现批量更新接口
- [ ] 前端添加批量操作按钮

### 7.5 数据看板（P2）

- [ ] 实现统计接口
- [ ] 开发看板页面
- [ ] 添加图表展示

---

## 8. 部署说明

### 8.1 环境要求

- Python 3.8+
- StarRocks 3.x
- 至少 2GB 可用内存

### 8.2 依赖安装

```bash
pip install fastapi uvicorn pymysql pandas openpyxl xlrd pyyaml
```

### 8.3 启动服务

```bash
# 开发环境
python app.py

# 生产环境
uvicorn app:app --host 0.0.0.0 --port 11219 --workers 4
```

### 8.4 访问地址

- 前端页面: `http://<server>:11219/`
- API 文档: `http://<server>:11219/docs`

---

## 9. 附录

### 9.1 配置文件示例

```yaml
# StarRocks 数据库配置
starrocks:
  host: <starrocks-host>
  port: 9030
  user: root
  password: <password>
  database: <database>
  charset: utf8
```

### 9.2 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2026-05 | 初始版本，基于 MySQL |
| 2.0.0 | 待定 | 迁移至 StarRocks，新增审核和历史功能 |

---

*文档版本：1.0.0*
*最后更新：2026-05-27*
