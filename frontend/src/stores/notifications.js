import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { getAccessToken } from '../api/tokenStore'
import { t } from '../composables/useLocale'

const MAX_NOTIFICATIONS = 50
const INITIAL_RECONNECT_DELAY = 1000
const MAX_RECONNECT_DELAY = 30000

function buildSocketUrl() {
  const apiUrl = import.meta.env.VITE_API_URL || '/api'
  const url = new URL(apiUrl, window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `${url.pathname.replace(/\/$/, '')}/ws/notifications`
  url.search = ''
  return url.toString()
}

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref([])
  const connected = ref(false)
  const connecting = ref(false)
  const lastError = ref(null)
  const unreadCount = computed(() => notifications.value.filter((item) => !item.read).length)

  let socket = null
  let reconnectTimer = null
  let reconnectAttempt = 0
  let manuallyClosed = false

  function addNotification(notification) {
    if (!notification?.id || notification.type === 'connected' || notification.type === 'pong') return
    if (notifications.value.some((item) => item.id === notification.id)) return
    notifications.value.unshift({ ...notification, read: false })
    notifications.value = notifications.value.slice(0, MAX_NOTIFICATIONS)
  }

  function scheduleReconnect() {
    if (manuallyClosed || reconnectTimer || !getAccessToken()) return
    const delay = Math.min(INITIAL_RECONNECT_DELAY * 2 ** reconnectAttempt, MAX_RECONNECT_DELAY)
    reconnectAttempt += 1
    reconnectTimer = window.setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  function connect() {
    if (typeof WebSocket === 'undefined' || !getAccessToken()) return
    if (socket && [WebSocket.OPEN, WebSocket.CONNECTING].includes(socket.readyState)) return

    manuallyClosed = false
    connecting.value = true
    lastError.value = null
    socket = new WebSocket(buildSocketUrl())

    socket.onopen = () => {
      socket.send(JSON.stringify({ type: 'auth', token: getAccessToken() }))
      connected.value = true
      connecting.value = false
      reconnectAttempt = 0
    }
    socket.onmessage = (event) => {
      try {
        addNotification(JSON.parse(event.data))
      } catch {
        lastError.value = t('notifications.parseError')
      }
    }
    socket.onerror = () => {
      lastError.value = t('notifications.connectionError')
    }
    socket.onclose = () => {
      connected.value = false
      connecting.value = false
      socket = null
      scheduleReconnect()
    }
  }

  function disconnect() {
    manuallyClosed = true
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket) socket.close()
    socket = null
    connected.value = false
    connecting.value = false
  }

  function markRead(id) {
    const item = notifications.value.find((notification) => notification.id === id)
    if (item) item.read = true
  }

  function markAllRead() {
    notifications.value.forEach((item) => { item.read = true })
  }

  function clear() {
    notifications.value = []
  }

  return {
    notifications,
    connected,
    connecting,
    lastError,
    unreadCount,
    connect,
    disconnect,
    addNotification,
    markRead,
    markAllRead,
    clear,
  }
})
