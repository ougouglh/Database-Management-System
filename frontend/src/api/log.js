import request from './index'

export const logApi = {
  // 获取操作日志列表
  getOperationLogs(params) {
    return request({
      url: '/logs/operations',
      method: 'GET',
      params
    })
  },

  // 获取日志统计
  getLogStats() {
    return request({
      url: '/logs/stats',
      method: 'GET'
    })
  },

  // 导出日志（待实现）
  exportLogs(params) {
    return request({
      url: '/logs/export',
      method: 'POST',
      params,
      responseType: 'blob'
    })
  }
}
