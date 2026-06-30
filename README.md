# 商品条码数据管理系统

一个极简、高效的内网商品数据导入导出系统，用于管理多方平台商品条码信息的汇总与维护。

## 项目简介

本系统主要用于管理和维护数据库多表数据，支持多平台（MSY、EB、MT、GS1）商品信息的统一管理、导入、导出、查询和编辑。

### 核心功能

- **数据导入** - 支持 Excel/CSV 批量导入，包含预览和校验功能
- **数据导出** - 支持全量数据导出为 Excel 或 CSV 格式
- **数据查询** - 分页展示、关键词搜索、多字段模糊匹配
- **在线编辑** - 支持单条记录在线修改
- **用户认证** - 基于 JWT 的登录认证和权限管理
- **操作日志** - 记录所有操作行为，支持审计追溯

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | HTML5/CSS3/JavaScript | 原生实现，响应式设计 |
| 前端 | Vue 3 + Element Plus | 新版管理界面 |
| 后端 | Python 3.x | 开发语言 |
| 后端 | FastAPI | Web 框架 |
| 后端 | PyMySQL | 数据库驱动 |
| 后端 | Pandas | 数据处理 |
| 数据库 | MySQL / StarRocks | 数据存储 |

## 快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+ / StarRocks 3.x
- 至少 2GB 可用内存

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置数据库

编辑 `config.yaml` 文件，设置数据库连接信息：

```yaml
mysql1:
  host: 192.168.239.131
  port: 3306
  user: root
  password: your_password
  database: bigdata_main_data2
  charset: utf8mb4
```

### 启动服务

**Windows 系统：**
```bash
start_server.bat
```

**Linux/Mac 系统：**
```bash
chmod +x start_server.sh
./start_server.sh
```

**手动启动：**
```bash
python app.py
```

### 访问系统

启动后访问：`http://localhost:11219`

## 功能说明

### 1. 数据导入

- 支持 `.xlsx`、`.xls`、`.csv` 格式
- 文件必须包含 `item_barcode` 和 `new_name` 列
- 导入前可预览新增/更新/跳过的记录
- 相同条码自动覆盖更新

### 2. 数据导出

- 导出全量表数据
- 支持 Excel 和 CSV 两种格式
- 文件名自动添加时间戳
- 自动处理特殊字符

### 3. 数据查询

- 分页展示（默认 50 条/页）
- 支持关键词搜索（9 个字段模糊匹配）
- 可搜索字段：item_barcode、item_name、new_name、msy_item_name、eb_item_name、mt_item_name、gs1_item_name、old_cat_name、new_cat_name

### 4. 在线编辑

- 点击 `new_name` 字段即可编辑
- 即时保存生效

### 5. 用户认证

- 用户名/密码登录
- Session 会话管理
- 自动登出（超时 8 小时）

## 项目结构

```
mysql/
├── app.py                      # FastAPI 主应用
├── config.yaml                 # 配置文件
├── requirements.txt            # Python 依赖
├── create_table.sql            # 建表 SQL
├── create_auth_tables.sql      # 用户认证表 SQL
├── start_server.bat            # Windows 启动脚本
├── start_server.sh             # Linux/Mac 启动脚本
├── api/                        # API 模块
│   ├── auth.py                # 认证接口
│   └── log.py                 # 日志接口
├── data_tools/                 # 数据工具
│   ├── validator.py           # 数据校验
│   └── query_builder.py       # 查询构建
├── utils/                      # 工具模块
│   └── db.py                  # 数据库连接
├── static/                     # 静态资源
│   ├── index.html             # 主页面
│   ├── login.html             # 登录页面
│   ├── styles.css             # 样式文件
│   ├── script.js              # 前端脚本
│   └── exports/               # 导出文件目录
├── frontend/                   # Vue 3 前端项目
│   ├── src/
│   │   ├── main.js
│   │   ├── api/
│   │   └── views/
│   └── package.json
└── docs/                       # 文档目录
    ├── TECH_DOC.md            # 技术文档
    └── 需求文档_多阶段导入导出系统.md
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 登录页面 |
| GET | `/main` | 主页面 |
| GET | `/api/health` | 健康检查 |
| POST | `/api/auth/login` | 用户登录 |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/import` | 数据导入 |
| POST | `/api/validate` | 数据校验 |
| POST | `/api/preview` | 变更预览 |
| GET | `/api/data` | 获取数据（分页、搜索） |
| GET | `/api/export` | 导出数据 |
| PUT | `/api/update` | 更新单条记录 |
| GET | `/api/stats` | 统计信息 |
| GET | `/api/tables` | 获取所有表 |
| GET | `/api/tables/{table}/columns` | 获取表字段 |
| POST | `/api/query/preview` | 查询预览 |
| POST | `/api/query/export` | 查询导出 |
| POST | `/api/query/update/preview` | 更新预览 |
| POST | `/api/query/update/execute` | 执行更新 |

详细 API 文档请访问：`http://localhost:11219/docs`

### 认证相关表

详见 `create_auth_tables.sql` 文件。

## 常见问题

**Q: 无法访问网页？**

A: 检查防火墙设置，确保 11219 端口开放。

**Q: 导入失败？**

A: 确保文件包含 item_barcode 和 new_name 两列，第一行为列名。

**Q: 数据库连接失败？**

A: 检查 config.yaml 中的数据库配置是否正确。

## 版本信息

- 版本: 1.0.0
- 更新日期: 2026-06-30
- 许可: 内部使用

## 扩展计划

- [ ] 数据审核流程
- [ ] 变更历史记录
- [ ] 批量操作功能
- [ ] 数据质量看板
- [ ] StarRocks 迁移支持

---

*内部系统 - 请勿外传*
