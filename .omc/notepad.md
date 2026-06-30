# Notepad
<!-- Auto-managed by OMC. Manual edits preserved in MANUAL section. -->

## Priority Context
<!-- ALWAYS loaded. Keep under 500 chars. Critical discoveries only. -->

## Working Memory
<!-- Session notes. Auto-pruned after 7 days. -->
### 2026-06-15 09:09
# 项目概览
**项目名称**: 内网数据导入导出系统（多阶段商品数据管理系统）
**用途**: 管理69开头TOP96增量商品条码信息，支持5阶段数据流转

# 技术栈
**后端**: FastAPI + Python 3.x + PyMySQL + Pandas
**前端**: Vue 3 + Element Plus + Vite + Pinia + Vue Router
**数据库**: MySQL (bigdata_main_data2)
**认证**: JWT + BCrypt
**端口**: 11219

# 核心表
barcode_base_info_69_top96_incre_allplatform_name (主表)
data_sync_sys_user (用户表)
data_sync_sys_operation_log (操作日志表)

# 目录结构
- app.py: FastAPI主应用
- config.yaml: 配置文件(数据库连接、JWT密钥、阶段配置)
- api/: 路由模块(auth.py, log.py)
- utils/: 工具类(db.py, security.py)
- data_tools/: QueryBuilder, SQLValidator
- data_validator.py: 数据校验模块
- frontend/: Vue3前端项目

# API端点
认证: /api/auth/login, /api/auth/logout
数据: /api/validate, /api/preview, /api/import, /api/export, /api/data
日志: /api/logs/operations
工具: /api/tables, /api/query/preview, /api/query/export

# 五阶段配置(当前都指向同一张表)
1. 品类定义(category_definition)
2. 分类处理(classification_processing)  
3. 第三方校验(third_party_validation)
4. Mapping管理(enterprise_brand_mapping)
5. 最终版本(final_product)

# 导入流程
上传文件 → 数据校验 → 变更预览 → 确认导入(分块事务)



## MANUAL
<!-- User content. Never auto-pruned. -->

