import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi } from '@/api/auth'

export const useUserStore = defineStore(
  'user',
  () => {
    const token = ref(localStorage.getItem('token') || '')
    const userInfo = ref(null)

    // 是否已登录
    const isLoggedIn = () => !!token.value

    // 登录
    const login = async (username, password) => {
      const res = await authApi.login({ username, password })
      token.value = res.access_token
      userInfo.value = res.user
      localStorage.setItem('token', token.value)
      return res
    }

    // 登出
    const logout = async () => {
      try {
        await authApi.logout()
      } catch (e) {
        console.error('登出请求失败:', e)
      } finally {
        token.value = ''
        userInfo.value = null
        localStorage.removeItem('token')
      }
    }

    // 获取用户信息
    const fetchUserInfo = async () => {
      const res = await authApi.getUserInfo()
      userInfo.value = res
      return res
    }

    return {
      token,
      userInfo,
      isLoggedIn,
      login,
      logout,
      fetchUserInfo
    }
  }
)
