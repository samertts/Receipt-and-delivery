import MockAdapter from 'axios-mock-adapter'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import client from '../src/api/client'
import { authApi } from '../src/api'
import {
  clearSession,
  getAccessToken,
  getRefreshToken,
  getSessionUser,
  setSession,
} from '../src/api/tokenStore'
import { useAuthStore } from '../src/stores/auth'

const mock = new MockAdapter(client)

function jwtFor(payload) {
  const encode = (value) => btoa(JSON.stringify(value)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode(payload)}.signature`
}

describe('API client and authentication integration', () => {
  beforeEach(() => {
    mock.reset()
    setActivePinia(createPinia())
    clearSession()
  })

  afterEach(() => {
    mock.reset()
    vi.restoreAllMocks()
  })

  it('unwraps the API envelope while preserving metadata and message', async () => {
    mock.onGet('/transactions').reply(200, {
      success: true,
      message: 'تم جلب المعاملات',
      data: [{ id: 'txn-1' }],
      meta: { page: 2, per_page: 20, total: 41 },
    })

    const response = await client.get('/transactions')

    expect(response.data).toEqual([{ id: 'txn-1' }])
    expect(response.meta).toMatchObject({ page: 2, per_page: 20, total: 41 })
    expect(response.message).toBe('تم جلب المعاملات')
    expect(response.envelope.success).toBe(true)
  })

  it('refreshes an expired access token and retries the original request', async () => {
    const oldAccessToken = 'expired-access-token'
    const refreshToken = 'valid-refresh-token'
    const newAccessToken = 'new-access-token'
    setSession({ accessToken: oldAccessToken, refreshToken })

    mock.onGet('/transactions').replyOnce(401, {
      success: false,
      message: 'انتهت الجلسة',
      data: null,
      meta: { error_code: 'TOKEN_EXPIRED' },
    })
    mock.onPost('/auth/refresh', { refresh_token: refreshToken }).reply(200, {
      success: true,
      message: 'تم تحديث الرمز',
      data: { access_token: newAccessToken, refresh_token: 'rotated-refresh-token' },
      meta: {},
    })
    mock.onGet('/transactions').reply(200, {
      success: true,
      message: '',
      data: [{ id: 'txn-after-refresh' }],
      meta: { total: 1 },
    })

    const response = await client.get('/transactions')

    expect(response.data).toEqual([{ id: 'txn-after-refresh' }])
    expect(getAccessToken()).toBe(newAccessToken)
    expect(getRefreshToken()).toBe('rotated-refresh-token')
    expect(mock.history.get).toHaveLength(2)
    expect(mock.history.get[1].headers.Authorization).toBe(`Bearer ${newAccessToken}`)
  })

  it('logs in through the store and persists the decoded user and tokens', async () => {
    const accessToken = jwtFor({ sub: 'lab-admin', role: 'admin' })
    vi.spyOn(authApi, 'login').mockResolvedValue({
      data: { access_token: accessToken, refresh_token: 'refresh-1' },
    })

    const store = useAuthStore()
    const user = await store.login('lab-admin', 'Admin@123')

    expect(user).toEqual({ username: 'lab-admin', role: 'admin' })
    expect(store.isAuthenticated).toBe(true)
    expect(store.isAdmin).toBe(true)
    expect(getAccessToken()).toBe(accessToken)
    expect(getRefreshToken()).toBe('refresh-1')
    expect(getSessionUser()).toEqual({ username: 'lab-admin', role: 'admin' })
  })

  it('rotates tokens when the store explicitly refreshes the session', async () => {
    setSession({ accessToken: 'old-access', refreshToken: 'old-refresh', user: { username: 'user1', role: 'user' } })
    vi.spyOn(authApi, 'refresh').mockResolvedValue({
      data: { access_token: 'new-access', refresh_token: 'new-refresh' },
    })

    const store = useAuthStore()
    const token = await store.refresh()

    expect(token).toBe('new-access')
    expect(store.token).toBe('new-access')
    expect(store.refreshToken).toBe('new-refresh')
    expect(getAccessToken()).toBe('new-access')
    expect(getRefreshToken()).toBe('new-refresh')
  })
})

