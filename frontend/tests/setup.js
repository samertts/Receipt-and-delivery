import { afterEach, beforeEach, vi } from 'vitest'
import { clearSession } from '../src/api/tokenStore'

beforeEach(() => {
  clearSession()
  window.history.replaceState({}, '', '/')
})

afterEach(() => {
  vi.restoreAllMocks()
})

