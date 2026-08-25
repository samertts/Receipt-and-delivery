import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Reports from '../src/pages/Reports.vue'
import { reportsApi } from '../src/api'

const reportPayload = {
  filters: { start_date: null, end_date: null, status: null, transaction_type: null },
  summary: {
    total: 2,
    by_status: { approved: 1, draft: 1, rejected: 0, archived: 0, cancelled: 0 },
    by_type: { استلام: 1, تسليم: 1 },
  },
  transactions: [
    {
      id: 'txn-1',
      transaction_no: 'TXN-001',
      transaction_type: 'استلام',
      sender_name: 'مختبر بغداد',
      receiver_name: 'مختبر الكرخ',
      status: 'approved',
      transaction_date: '2026-08-24',
    },
    {
      id: 'txn-2',
      transaction_no: 'TXN-002',
      transaction_type: 'تسليم',
      sender_name: 'مختبر الرصافة',
      receiver_name: 'مختبر الأعظمية',
      status: 'draft',
      transaction_date: '2026-08-23',
    },
  ],
}

describe('reports UI/API integration', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('loads filtered report data and renders statistics and transaction preview', async () => {
    vi.spyOn(reportsApi, 'summary').mockResolvedValue({ data: reportPayload })

    const wrapper = mount(Reports)
    await flushPromises()

    expect(reportsApi.summary).toHaveBeenCalledWith({ lang: 'ar' })
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('TXN-001')
    expect(wrapper.text()).toContain('مختبر بغداد')
    expect(wrapper.text()).toContain('استلام')

    await wrapper.get('#status-filter').setValue('approved')
    await wrapper.get('form').trigger('submit.prevent')
    await flushPromises()

    expect(reportsApi.summary).toHaveBeenLastCalledWith({ status: 'approved', lang: 'ar' })
  })

  it('downloads an Excel report with the active filters', async () => {
    vi.spyOn(reportsApi, 'summary').mockResolvedValue({ data: reportPayload })
    vi.spyOn(reportsApi, 'exportExcel').mockResolvedValue({ data: new Blob(['xlsx']) })
    const createObjectURL = vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:report')
    const revokeObjectURL = vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {})
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    const wrapper = mount(Reports)
    await flushPromises()
    await wrapper.get('#type-filter').setValue('استلام')
    const excelButton = wrapper.findAll('button').find((button) => button.text().includes('Excel'))
    await excelButton.trigger('click')
    await flushPromises()

    expect(reportsApi.exportExcel).toHaveBeenCalledWith({ transaction_type: 'استلام', lang: 'ar' })
    expect(createObjectURL).toHaveBeenCalled()
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:report')
  })
})

