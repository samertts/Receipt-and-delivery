import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { transactionsApi } from '../src/api'
import { useTransactionStore } from '../src/stores/transactions'

describe('transactions store and API integration', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.restoreAllMocks()
  })

  it('loads paginated transactions using meta.total from the API envelope', async () => {
    vi.spyOn(transactionsApi, 'list').mockResolvedValue({
      data: [{ id: 'txn-1', transaction_no: 'LAB-2026-000001' }],
      meta: { page: 2, per_page: 20, total: 41 },
    })

    const store = useTransactionStore()
    await store.fetchList({ page: 2, limit: 20, status: 'received' })

    expect(transactionsApi.list).toHaveBeenCalledWith({ page: 2, limit: 20, status: 'received' })
    expect(store.items).toHaveLength(1)
    expect(store.items[0].transaction_no).toBe('LAB-2026-000001')
    expect(store.total).toBe(41)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('creates, updates, and removes a transaction while keeping list and current state consistent', async () => {
    const original = { id: 'txn-1', status: 'received' }
    const created = { id: 'txn-2', status: 'draft' }
    const updated = { id: 'txn-1', status: 'delivered' }

    vi.spyOn(transactionsApi, 'create').mockResolvedValue({ data: created })
    vi.spyOn(transactionsApi, 'update').mockResolvedValue({ data: updated })
    vi.spyOn(transactionsApi, 'delete').mockResolvedValue({ status: 204 })

    const store = useTransactionStore()
    store.items.push(original)

    expect(await store.create({ status: 'draft' })).toEqual(created)
    expect(store.items[0]).toEqual(created)

    expect(await store.update('txn-1', { status: 'delivered' })).toEqual(updated)
    expect(store.items.find((item) => item.id === 'txn-1')).toEqual(updated)
    expect(store.current).toEqual(updated)

    await store.remove('txn-2')
    expect(store.items.some((item) => item.id === 'txn-2')).toBe(false)
    expect(transactionsApi.delete).toHaveBeenCalledWith('txn-2')
  })

  it('uses the normalized API error message and always resets loading', async () => {
    const apiError = new Error('request failed')
    apiError.apiMessage = 'لا يمكن تحميل المعاملات الآن'
    vi.spyOn(transactionsApi, 'list').mockRejectedValue(apiError)

    const store = useTransactionStore()
    await expect(store.fetchList()).rejects.toBe(apiError)

    expect(store.error).toBe('لا يمكن تحميل المعاملات الآن')
    expect(store.loading).toBe(false)
  })
})

