import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const routerPush = vi.hoisted(() => vi.fn())

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: routerPush }),
}))

import Login from '../src/pages/Login.vue'
import { authApi } from '../src/api'

function mountLogin() {
  setActivePinia(createPinia())
  return mount(Login, {
    global: {
      plugins: [createPinia()],
    },
  })
}

describe('login page UI/API integration', () => {
  beforeEach(() => {
    routerPush.mockReset()
    vi.restoreAllMocks()
  })

  it('submits credentials through the API and navigates after success', async () => {
    const encode = (value) => btoa(JSON.stringify(value)).replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_')
    const accessToken = `${encode({ alg: 'none' })}.${encode({ sub: 'admin', role: 'admin' })}.signature`
    vi.spyOn(authApi, 'login').mockResolvedValue({
      data: { access_token: accessToken, refresh_token: 'refresh-token' },
    })

    const wrapper = mountLogin()
    await wrapper.get('#username').setValue('admin')
    await wrapper.get('#password').setValue('Admin@123')
    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()

    expect(authApi.login).toHaveBeenCalledWith({ username: 'admin', password: 'Admin@123' })
    expect(routerPush).toHaveBeenCalledWith('/dashboard')
    expect(wrapper.text()).not.toContain('فشل تسجيل الدخول')
  })

  it('renders the normalized Backend error message and re-enables the form', async () => {
    const error = new Error('invalid credentials')
    error.apiMessage = 'اسم المستخدم أو كلمة المرور غير صحيحة'
    vi.spyOn(authApi, 'login').mockRejectedValue(error)

    const wrapper = mountLogin()
    await wrapper.get('#username').setValue('wrong')
    await wrapper.get('#password').setValue('Wrong@123')
    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain('اسم المستخدم أو كلمة المرور غير صحيحة')
    expect(wrapper.get('button').attributes('disabled')).toBeUndefined()
    expect(routerPush).not.toHaveBeenCalled()
  })
})

