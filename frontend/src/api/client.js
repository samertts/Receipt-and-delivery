import axios from 'axios'
import { clearSession, getAccessToken, getRefreshToken, updateAccessToken, updateRefreshToken } from './tokenStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let failedQueue = []

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token)
  })
  failedQueue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url.endsWith('/auth/refresh')) {
      originalRequest._retry = true
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        clearSession()
        window.location.href = '/'
        return Promise.reject(error)
      }
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return client(originalRequest)
        })
      }
      isRefreshing = true
      try {
        const response = await client.post('/auth/refresh', { refresh_token: refreshToken })
        const newToken = response.data.access_token
        updateAccessToken(newToken)
        if (response.data.refresh_token) updateRefreshToken(response.data.refresh_token)
        processQueue(null, newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return client(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearSession()
        window.location.href = '/'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)

export default client
