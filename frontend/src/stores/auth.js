import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  getSessionUser,
  setSession,
  updateAccessToken,
  updateRefreshToken,
} from '../api/tokenStore'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(getSessionUser())
  const token = ref(getAccessToken())
  const refreshToken = ref(getRefreshToken())
  const permissions = ref(getSessionUser()?.permissions || [])
  const roles = ref(getSessionUser()?.roles || [])

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || '')

  function decodeTokenPayload(value) {
    try {
      return JSON.parse(atob(value.split('.')[1]))
    } catch {
      return null
    }
  }

  async function login(username, password) {
    const response = await authApi.login({ username, password })
    token.value = response.data.access_token
    refreshToken.value = response.data.refresh_token || ''
    const payload = decodeTokenPayload(token.value)
    user.value = { username: payload?.sub || username, role: payload?.role || '' }
    if (Array.isArray(payload?.permissions)) {
      user.value.permissions = payload.permissions
      permissions.value = payload.permissions
    } else {
      permissions.value = []
    }
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
      const payload = decodeTokenPayload(token.value)
      if (payload) {
        user.value = { ...(user.value || {}), username: payload.sub, role: payload.role }
        if (Array.isArray(payload.permissions)) {
          user.value.permissions = payload.permissions
          permissions.value = payload.permissions
        }
      }
      setSession({ accessToken: token.value, refreshToken: refreshToken.value, user: user.value })
      return token.value
    } catch {
      logout()
      return null
    }
  }

  function hasPermission(permission) {
    return permissions.value.includes(permission)
  }

  function hasAnyPermission(required) {
    return required.some((permission) => hasPermission(permission))
  }

  async function loadProfile() {
    if (!token.value) return null
    const response = await authApi.me()
    const profile = response.data
    user.value = { ...user.value, ...profile }
    permissions.value = profile.permissions || []
    roles.value = profile.roles || []
    setSession({ accessToken: token.value, refreshToken: refreshToken.value, user: user.value })
    return profile
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch {
      // server logout is best-effort
    }
    user.value = null
    permissions.value = []
    roles.value = []
    token.value = ''
    refreshToken.value = ''
    clearSession()
  }

  async function changePassword(currentPassword, newPassword) {
    await authApi.changePassword({ current_password: currentPassword, new_password: newPassword })
  }

  return { user, token, refreshToken, permissions, roles, isAuthenticated, isAdmin, userRole, hasPermission, hasAnyPermission, loadProfile, login, refresh, logout, changePassword }
})
