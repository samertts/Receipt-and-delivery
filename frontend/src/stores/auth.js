import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || '')

  async function login(username, password) {
    const response = await authApi.login({ username, password })
    token.value = response.data.access_token
    refreshToken.value = response.data.refresh_token || ''
    localStorage.setItem('access_token', response.data.access_token)
    if (refreshToken.value) localStorage.setItem('refresh_token', refreshToken.value)

    const payload = JSON.parse(atob(response.data.access_token.split('.')[1]))
    user.value = { username: payload.sub, role: payload.role }
    localStorage.setItem('user', JSON.stringify(user.value))
    return user.value
  }

  async function refresh() {
    if (!refreshToken.value) return null
    try {
      const response = await authApi.refresh({ refresh_token: refreshToken.value })
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token || ''
      localStorage.setItem('access_token', response.data.access_token)
      if (refreshToken.value) localStorage.setItem('refresh_token', refreshToken.value)
      return token.value
    } catch {
      logout()
      return null
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // server logout is best-effort
    }
    user.value = null
    token.value = ''
    refreshToken.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  async function changePassword(currentPassword, newPassword) {
    await authApi.changePassword({ current_password: currentPassword, new_password: newPassword })
  }

  return { user, token, refreshToken, isAuthenticated, isAdmin, userRole, login, refresh, logout, changePassword }
})
