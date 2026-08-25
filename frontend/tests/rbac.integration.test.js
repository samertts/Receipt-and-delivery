import { createPinia, setActivePinia } from 'pinia'
import { afterEach, describe, expect, it, vi } from 'vitest'

const authApiMock = vi.hoisted(() => ({
  login: vi.fn(),
  logout: vi.fn(),
  refresh: vi.fn(),
  me: vi.fn(),
}))

vi.mock('../src/api', () => ({ authApi: authApiMock }))

import { useAuthStore } from '../src/stores/auth'

function tokenFor(payload) {
  const encode = (value) => btoa(JSON.stringify(value)).replace(/=/g, '')
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode(payload)}.signature`
}

describe('RBAC integration', () => {
  afterEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('stores permissions from the access token and evaluates them by role', async () => {
    setActivePinia(createPinia())
    authApiMock.login.mockResolvedValue({
      data: {
        access_token: tokenFor({ sub: 'supervisor', role: 'supervisor', permissions: ['view_dashboard', 'view_reports'] }),
        refresh_token: 'refresh-token',
      },
    })

    const auth = useAuthStore()
    await auth.login('supervisor', 'password')

    expect(auth.hasPermission('view_dashboard')).toBe(true)
    expect(auth.hasPermission('view_reports')).toBe(true)
    expect(auth.hasPermission('manage_users')).toBe(false)
    expect(auth.hasAnyPermission(['manage_users', 'view_reports'])).toBe(true)
  })

  it('refreshes permissions when the backend rotates the access token', async () => {
    setActivePinia(createPinia())
    authApiMock.login.mockResolvedValue({
      data: { access_token: tokenFor({ sub: 'user', role: 'user', permissions: ['view_dashboard'] }), refresh_token: 'refresh-1' },
    })
    authApiMock.refresh.mockResolvedValue({
      data: { access_token: tokenFor({ sub: 'user', role: 'user', permissions: ['view_dashboard', 'create_transaction'] }), refresh_token: 'refresh-2' },
    })

    const auth = useAuthStore()
    await auth.login('user', 'password')
    await auth.refresh()

    expect(auth.hasPermission('create_transaction')).toBe(true)
    expect(auth.refreshToken).toBe('refresh-2')
  })
})
