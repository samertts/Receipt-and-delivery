import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { clearSession, setSession } from '../src/api/tokenStore'
import { useNotificationStore } from '../src/stores/notifications'

class FakeWebSocket {
  static CONNECTING = 0
  static OPEN = 1
  static CLOSED = 3
  static instances = []

  constructor(url) {
    this.url = url
    this.readyState = FakeWebSocket.CONNECTING
    this.sent = []
    FakeWebSocket.instances.push(this)
  }

  send(payload) {
    this.sent.push(payload)
  }

  open() {
    this.readyState = FakeWebSocket.OPEN
    this.onopen?.()
  }

  emit(payload) {
    this.onmessage?.({ data: JSON.stringify(payload) })
  }

  close() {
    this.readyState = FakeWebSocket.CLOSED
    this.onclose?.()
  }
}

describe('notifications store and WebSocket integration', () => {
  beforeEach(() => {
    FakeWebSocket.instances = []
    globalThis.WebSocket = FakeWebSocket
    setActivePinia(createPinia())
    setSession({ accessToken: 'access-token', user: { username: 'admin', role: 'admin' } })
  })

  it('connects with the access token and stores incoming transaction notifications', () => {
    const store = useNotificationStore()
    store.connect()
    const socket = FakeWebSocket.instances[0]

    expect(socket.url).toContain('/api/ws/notifications')
    expect(socket.url).not.toContain('access-token')
    socket.open()
    expect(JSON.parse(socket.sent[0])).toEqual({ type: 'auth', token: 'access-token' })
    socket.emit({ type: 'connected', message: 'جاهز' })
    socket.emit({
      id: 'notification-1',
      type: 'transaction',
      event: 'updated',
      title: 'تم تحديث معاملة',
      message: 'LAB-2026-000001 — الحالة: approved',
      transaction_id: 'txn-1',
      created_at: '2026-08-24T20:00:00+00:00',
    })
    socket.emit({
      id: 'notification-1',
      type: 'transaction',
      event: 'updated',
      title: 'تم تحديث معاملة',
      message: 'نسخة مكررة',
    })

    expect(store.connected).toBe(true)
    expect(store.notifications).toHaveLength(1)
    expect(store.unreadCount).toBe(1)
    expect(store.notifications[0].message).toContain('LAB-2026-000001')

    store.markRead('notification-1')
    expect(store.unreadCount).toBe(0)
    store.disconnect()
    expect(store.connected).toBe(false)
  })

  it('marks all notifications as read and clears the local inbox', () => {
    const store = useNotificationStore()
    store.addNotification({ id: 'one', type: 'transaction', title: 'أول', message: '1' })
    store.addNotification({ id: 'two', type: 'transaction', title: 'ثانٍ', message: '2' })

    expect(store.unreadCount).toBe(2)
    store.markAllRead()
    expect(store.unreadCount).toBe(0)
    store.clear()
    expect(store.notifications).toEqual([])
  })

  it('does not connect without an access token', () => {
    clearSession()
    const store = useNotificationStore()
    store.connect()

    expect(FakeWebSocket.instances).toHaveLength(0)
    expect(store.connected).toBe(false)
  })
})

