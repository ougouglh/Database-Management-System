import request from './index'

export const dataApi = {
  // 获取数据列表（分页）
  getDataList(params) {
    return request({
      url: '/data',
      method: 'GET',
      params
    })
  },

  // 获取统计信息
  getStats() {
    return request({
      url: '/stats',
      method: 'GET'
    })
  },

  // 获取表列表
  getTables() {
    return request({
      url: '/tables',
      method: 'GET'
    })
  },

  // 获取表字段
  getTableColumns(table) {
    return request({
      url: `/tables/${table}/columns`,
      method: 'GET'
    })
  },

  // 文件校验
  validateFile(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: '/validate',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 变更预览
  previewChanges(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: '/preview',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  // 数据导入
  importData(file) {
    const formData = new FormData()
    formData.append('file', file)
    return request({
      url: '/import',
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 60000 // 导入可能需要更长时间
    })
  },

  // 单条更新
  updateData(itemBarcode, newName) {
    return request({
      url: '/update',
      method: 'PUT',
      data: {
        item_barcode: itemBarcode,
        new_name: newName
      }
    })
  },

  // 数据导出
  exportData(params) {
    return request({
      url: '/export',
      method: 'GET',
      params,
      responseType: 'blob'
    })
  },

  // SQL 预览
  previewQuery(data) {
    return request({
      url: '/query/preview',
      method: 'POST',
      data
    })
  },

  // SQL 导出
  exportQuery(data) {
    return request({
      url: '/query/export',
      method: 'POST',
      data,
      responseType: 'blob'
    })
  },

  // 更新预览
  previewUpdate(data) {
    return request({
      url: '/query/update/preview',
      method: 'POST',
      data
    })
  },

  // 执行更新
  executeUpdate(data) {
    return request({
      url: '/query/update/execute',
      method: 'POST',
      data
    })
  }
}
