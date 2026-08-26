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

function profile(overrides = {}) {
  return {
    id: 'user-1',
    username: 'supervisor',
    full_name: 'Supervisor',
    role: 'supervisor',
    permissions: ['view_dashboard', 'view_reports'],
    roles: ['supervisor'],
    role_permissions: {},
    ...overrides,
  }
}

describe('RBAC integration', () => {
  afterEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('stores permissions from the server profile and evaluates them by role', async () => {
    setActivePinia(createPinia())
    authApiMock.login.mockResolvedValue({ data: { authenticated: true } })
    authApiMock.me.mockResolvedValue({ data: profile() })

    const auth = useAuthStore()
    await auth.login('supervisor', 'password')

    expect(auth.hasPermission('view_dashboard')).toBe(true)
    expect(auth.hasPermission('view_reports')).toBe(true)
    expect(auth.hasPermission('manage_users')).toBe(false)
    expect(auth.hasAnyPermission(['manage_users', 'view_reports'])).toBe(true)
  })

  it('refreshes permissions from the server profile after rotating the cookie session', async () => {
    setActivePinia(createPinia())
    authApiMock.login.mockResolvedValue({ data: { authenticated: true } })
    authApiMock.me
      .mockResolvedValueOnce({ data: profile({ role: 'user', permissions: ['view_dashboard'] }) })
      .mockResolvedValueOnce({ data: profile({ role: 'user', permissions: ['view_dashboard', 'create_transaction'] }) })
    authApiMock.refresh.mockResolvedValue({ data: { authenticated: true } })

    const auth = useAuthStore()
    await auth.login('user', 'password')
    await auth.refresh()

    expect(auth.hasPermission('create_transaction')).toBe(true)
    expect(auth.refreshToken).toBe('')
  })
})
