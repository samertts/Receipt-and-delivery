import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'
import { clearSession, getSessionUser, setSession, updateAccessToken, updateRefreshToken } from '../api/tokenStore'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(getSessionUser())
  const token = ref('')
  const refreshToken = ref('')

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || '')

  async function login(username, password) {
    const response = await authApi.login({ username, password })
    token.value = response.data.access_token
    refreshToken.value = response.data.refresh_token || ''
    const payload = JSON.parse(atob(response.data.access_token.split('.')[1]))
    user.value = { username: payload.sub, role: payload.role }
    setSession({ accessToken: token.value, refreshToken: refreshToken.value, user: user.value })
    return user.value
  }

  async function refresh() {
    if (!refreshToken.value) return null
    try {
      const response = await authApi.refresh({ refresh_token: refreshToken.value })
      token.value = response.data.access_token
      refreshToken.value = response.data.refresh_token || ''
      updateAccessToken(token.value)
      updateRefreshToken(refreshToken.value)
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
    clearSession()
  }

  async function changePassword(currentPassword, newPassword) {
    await authApi.changePassword({ current_password: currentPassword, new_password: newPassword })
  }

  return { user, token, refreshToken, isAuthenticated, isAdmin, userRole, login, refresh, logout, changePassword }
})
