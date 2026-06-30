import request from './index'

export const authApi = {
  // 登录
  login(data) {
    return request({
      url: '/auth/login',
      method: 'POST',
      data
    })
  },

  // 登出
  logout() {
    return request({
      url: '/auth/logout',
      method: 'POST'
    })
  },

  // 获取用户信息
  getUserInfo() {
    return request({
      url: '/auth/info',
      method: 'GET'
    })
  },

  // 验证 token
  verifyToken() {
    return request({
      url: '/auth/verify-token',
      method: 'GET'
    })
  },

  // 获取用户列表（管理员）
  getUserList(params) {
    return request({
      url: '/auth/users',
      method: 'GET',
      params
    })
  },

  // 创建用户（管理员）
  createUser(data) {
    return request({
      url: '/auth/users',
      method: 'POST',
      data
    })
  }
}
