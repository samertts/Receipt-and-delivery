import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('access_token') || '')

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const userRole = computed(() => user.value?.role || '')

  async function login(username, password) {
    const response = await authApi.login({ username, password })
    token.value = response.data.access_token
    localStorage.setItem('access_token', response.data.access_token)

    const payload = JSON.parse(atob(response.data.access_token.split('.')[1]))
    user.value = { username: payload.sub, role: payload.role }
    localStorage.setItem('user', JSON.stringify(user.value))
    return user.value
  }

  function logout() {
    user.value = null
    token.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
  }

  return { user, token, isAuthenticated, isAdmin, userRole, login, logout }
})
