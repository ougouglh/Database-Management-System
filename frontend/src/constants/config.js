/**
 * 全局应用配置
 */

// API 基础路径前缀（由 vite proxy 代理）
export const API_BASE = '/api'

// 应用基本信息
export const APP_INFO = {
  name: '内网数据导入导出系统',
  version: '1.0.0',
  description: 'barcode_base_info_69_top96_incre_allplatform_name 表数据管理',
  targetTable: 'barcode_base_info_69_top96_incre_allplatform_name'
}

// 表格分页
export const PAGE_SIZES = [20, 50, 100, 200]
export const DEFAULT_PAGE_SIZE = 20

// 文件上传限制
export const UPLOAD_CONFIG = {
  accept: '.xlsx,.xls,.csv',
  maxSizeMB: 50,
  timeout: 60000
}

// 导出格式
export const EXPORT_FORMATS = [
  { value: 'xlsx', label: 'Excel (.xlsx)' },
  { value: 'csv', label: 'CSV (.csv)' }
]

// 业务字段白名单（用于筛选/更新）
export const UPDATABLE_FIELDS = [
  { value: 'new_name', label: 'new_name' },
  { value: 'platform', label: 'platform' },
  { value: 'category', label: 'category' },
  { value: 'brand', label: 'brand' }
]

// 操作类型映射
export const OPERATION_TYPES = {
  login: { label: '登录', color: 'info' },
  logout: { label: '登出', color: 'info' },
  import: { label: '导入', color: 'success' },
  export: { label: '导出', color: 'warning' },
  view: { label: '查看', color: '' },
  edit: { label: '编辑', color: 'primary' },
  delete: { label: '删除', color: 'danger' }
}

export default {
  API_BASE,
  APP_INFO,
  PAGE_SIZES,
  DEFAULT_PAGE_SIZE,
  UPLOAD_CONFIG,
  EXPORT_FORMATS,
  UPDATABLE_FIELDS,
  OPERATION_TYPES
}
