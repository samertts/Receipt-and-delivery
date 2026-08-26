import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '../api'
import { clearSession, getSessionUser, setSession } from '../api/tokenStore'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(getSessionUser())
  // Kept as empty compatibility refs for components that only inspect store shape.
  const token = ref('')
  const refreshToken = ref('')
  const permissions = ref(user.value?.permissions || [])
  const roles = ref(user.value?.roles || [])
  const sessionLoaded = ref(false)

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || '')

  function applyProfile(profile) {
    user.value = profile
    permissions.value = profile?.permissions || []
    roles.value = profile?.roles || []
    setSession({ user: user.value })
    return profile
  }

  async function login(username, password) {
    await authApi.login({ username, password })
    return loadProfile(true)
  }

  async function refresh() {
    try {
      await authApi.refresh()
      return loadProfile(true)
    } catch {
      await logout(false)
      return null
    }
  }

  function hasPermission(permission) {
    return permissions.value.includes(permission)
  }

  function hasAnyPermission(required) {
    return required.some((permission) => hasPermission(permission))
  }

  async function loadProfile(force = false) {
    if (sessionLoaded.value && !force) return user.value
    try {
      const response = await authApi.me()
      return applyProfile(response.data)
    } catch (error) {
      user.value = null
      permissions.value = []
      roles.value = []
      clearSession()
      throw error
    } finally {
      sessionLoaded.value = true
    }
  }

  async function logout(notifyServer = true) {
    if (notifyServer) {
      try {
        await authApi.logout()
      } catch {
        // Server logout is best-effort; local state is always cleared.
      }
    }
    user.value = null
    permissions.value = []
    roles.value = []
    token.value = ''
    refreshToken.value = ''
    sessionLoaded.value = true
    clearSession()
  }

  async function changePassword(currentPassword, newPassword) {
    await authApi.changePassword({ current_password: currentPassword, new_password: newPassword })
  }

  return { user, token, refreshToken, permissions, roles, sessionLoaded, isAuthenticated, isAdmin, userRole, hasPermission, hasAnyPermission, loadProfile, login, refresh, logout, changePassword }
})
