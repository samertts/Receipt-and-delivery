import { createPinia, setActivePinia } from 'pinia'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import client from '../src/api/client'
import { authApi } from '../src/api'
import { clearSession, getAccessToken, getRefreshToken, getSessionUser, setSession } from '../src/api/tokenStore'
import { useAuthStore } from '../src/stores/auth'

const mock = new MockAdapter(client)

function profile(overrides = {}) {
  return {
    id: 'user-1',
    username: 'lab-admin',
    full_name: 'Lab Admin',
    role: 'admin',
    permissions: ['view_dashboard'],
    roles: ['admin'],
    role_permissions: {},
    ...overrides,
  }
}

describe('API client and cookie authentication integration', () => {
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
    expect(response.config.withCredentials).toBe(true)
  })

  it('refreshes the HttpOnly cookie session and retries the original request', async () => {
    mock.onGet('/transactions').replyOnce(401, {
      success: false,
      message: 'انتهت الجلسة',
      data: null,
      meta: { error_code: 'TOKEN_EXPIRED' },
    })
    mock.onPost('/auth/refresh').reply(200, {
      success: true,
      message: 'تم تحديث الجلسة',
      data: { authenticated: true },
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
    expect(mock.history.post[0].data).toBeUndefined()
    expect(mock.history.get).toHaveLength(2)
    expect(mock.history.get[1].headers.Authorization).toBeUndefined()
  })

  it('logs in through the store and loads the user profile without decoding or persisting JWTs', async () => {
    vi.spyOn(authApi, 'login').mockResolvedValue({ data: { authenticated: true } })
    vi.spyOn(authApi, 'me').mockResolvedValue({ data: profile() })

    const store = useAuthStore()
    const user = await store.login('lab-admin', 'Admin@123')

    expect(user).toEqual(profile())
    expect(store.isAuthenticated).toBe(true)
    expect(store.isAdmin).toBe(true)
    expect(getAccessToken()).toBe('')
    expect(getRefreshToken()).toBe('')
    expect(getSessionUser()).toEqual(profile())
  })

  it('refreshes the cookie session and reloads permissions from the profile endpoint', async () => {
    setSession({ user: profile({ role: 'user', permissions: ['view_dashboard'] }) })
    vi.spyOn(authApi, 'refresh').mockResolvedValue({ data: { authenticated: true } })
    vi.spyOn(authApi, 'me').mockResolvedValue({
      data: profile({ role: 'user', permissions: ['view_dashboard', 'create_transaction'] }),
    })

    const store = useAuthStore()
    const refreshedUser = await store.refresh()

    expect(refreshedUser.permissions).toContain('create_transaction')
    expect(store.token).toBe('')
    expect(store.refreshToken).toBe('')
    expect(getAccessToken()).toBe('')
    expect(getRefreshToken()).toBe('')
  })
})
