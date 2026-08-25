import { createPinia, setActivePinia } from 'pinia'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const routerPush = vi.hoisted(() => vi.fn())

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: routerPush }),
}))

import Dashboard from '../src/pages/Dashboard.vue'
import { dashboardApi } from '../src/api'

function mountDashboard() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(Dashboard, {
    global: {
      plugins: [pinia],
      stubs: { RouterLink: true },
    },
  })
}

describe('dashboard UI/API integration', () => {
  beforeEach(() => {
    routerPush.mockReset()
    vi.restoreAllMocks()
  })

  it('renders KPIs, daily trend bars, status distribution, and transaction types', async () => {
    vi.spyOn(dashboardApi, 'summary').mockResolvedValue({
      data: {
        summary: {
          total_transactions: 12,
          total_organizations: 4,
          by_status: { approved: 7, draft: 3, rejected: 2 },
        },
        trends: { total: 20, approved: 10, draft: -5, orgs: 4 },
        trend: [
          { date: '2026-08-18', count: 1 },
          { date: '2026-08-19', count: 3 },
          { date: '2026-08-20', count: 2 },
        ],
        by_type: [
          { key: 'استلام', count: 8 },
          { key: 'تسليم', count: 4 },
        ],
        recent_transactions: [],
      },
    })

    const wrapper = mountDashboard()
    await flushPromises()

    expect(dashboardApi.summary).toHaveBeenCalledWith({ days: 7, lang: 'ar' })
    expect(wrapper.text()).toContain('12')
    expect(wrapper.text()).toContain('4')
    expect(wrapper.text()).toContain('الاتجاه اليومي للمعاملات')
    expect(wrapper.text()).toContain('توزيع أنواع المعاملات')
    expect(wrapper.text()).toContain('استلام')
    expect(wrapper.find('[data-testid="dashboard-charts"] svg').exists()).toBe(true)
    expect(wrapper.find('[data-testid="smart-insights"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('توجد معاملات مرفوضة')
    expect(wrapper.findAll('[role="progressbar"]')).toHaveLength(5)
  })

  it('shows the retryable error state when the dashboard API fails', async () => {
    const error = new Error('dashboard unavailable')
    error.apiMessage = 'تعذر تحميل الإحصائيات'
    vi.spyOn(dashboardApi, 'summary').mockRejectedValue(error)

    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.get('[role="alert"]').text()).toContain('تعذر تحميل الإحصائيات')
    expect(wrapper.text()).toContain('إعادة المحاولة')
  })
})

