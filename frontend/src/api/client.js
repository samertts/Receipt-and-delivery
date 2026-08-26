import axios from 'axios'
import { clearSession } from './tokenStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
const UNSAFE_METHODS = new Set(['post', 'put', 'patch', 'delete'])

const client = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

function getCookie(name) {
  if (typeof document === 'undefined') return ''
  const prefix = `${encodeURIComponent(name)}=`
  const entry = document.cookie.split('; ').find((item) => item.startsWith(prefix))
  return entry ? decodeURIComponent(entry.slice(prefix.length)) : ''
}

client.interceptors.request.use((config) => {
  if (UNSAFE_METHODS.has((config.method || 'get').toLowerCase())) {
    const csrfToken = getCookie('lab_csrf_token')
    if (csrfToken) config.headers['X-CSRF-Token'] = csrfToken
  }
  return config
})

let isRefreshing = false
let failedQueue = []

function processQueue(error) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve()
  })
  failedQueue = []
}

client.interceptors.response.use(
  (response) => {
    const envelope = response.data
    if (
      envelope &&
      typeof envelope === 'object' &&
      envelope.success === true &&
      Object.prototype.hasOwnProperty.call(envelope, 'data')
    ) {
      response.envelope = envelope
      response.meta = envelope.meta || {}
      response.message = envelope.message || ''
      response.data = envelope.data
    }
    return response
  },
  async (error) => {
    const originalRequest = error.config || {}
    const errorPayload = error.response?.data
    if (errorPayload && typeof errorPayload === 'object') {
      error.apiMessage = errorPayload.message || errorPayload.detail || 'حدث خطأ غير متوقع'
      error.apiErrorCode = errorPayload.meta?.error_code || errorPayload.error_code || ''
      if (!errorPayload.detail) errorPayload.detail = error.apiMessage
    }
    if (error.response?.status === 401 && !originalRequest._retry && !originalRequest.url?.endsWith('/auth/refresh')) {
      originalRequest._retry = true
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(() => client(originalRequest))
      }
      isRefreshing = true
      try {
        await client.post('/auth/refresh')
        processQueue(null)
        return client(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError)
        clearSession()
        if (typeof window !== 'undefined') window.location.href = '/'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    return Promise.reject(error)
  },
)

export default client
