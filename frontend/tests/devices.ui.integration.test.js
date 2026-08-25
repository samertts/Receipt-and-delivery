import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Devices from '../src/pages/Devices.vue'

describe('devices UI integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok', printer_support: false }) }))
  })

  it('shows graceful unsupported states and keeps device actions safe', async () => {
    const wrapper = mount(Devices)
    await flushPromises()

    expect(wrapper.text()).toContain('الكاميرا غير مدعومة')
    expect(wrapper.text()).toContain('Web NFC غير مدعوم')
    expect(wrapper.find('button[disabled]').exists()).toBe(true)
    expect(wrapper.find('textarea').element.value).toBe('')
    expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:17321/health', expect.any(Object))
    wrapper.unmount()
  })
})
