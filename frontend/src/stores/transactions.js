import { defineStore } from 'pinia'
import { ref } from 'vue'
import { transactionsApi } from '../api'

export const useTransactionStore = defineStore('transactions', () => {
  const items = ref([])
  const current = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const total = ref(0)

  async function fetchList(params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await transactionsApi.list(params)
      items.value = response.data
      total.value = parseInt(response.headers['x-total-count'] || response.data.length)
    } catch (e) {
      error.value = e.response?.data?.detail || 'فشل في تحميل المعاملات'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchOne(id) {
    loading.value = true
    error.value = null
    try {
      const response = await transactionsApi.get(id)
      current.value = response.data
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'فشل في تحميل المعاملة'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function create(data) {
    loading.value = true
    error.value = null
    try {
      const response = await transactionsApi.create(data)
      items.value.unshift(response.data)
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'فشل في إنشاء المعاملة'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function update(id, data) {
    loading.value = true
    error.value = null
    try {
      const response = await transactionsApi.update(id, data)
      const idx = items.value.findIndex((i) => i.id === id)
      if (idx >= 0) items.value[idx] = response.data
      current.value = response.data
      return response.data
    } catch (e) {
      error.value = e.response?.data?.detail || 'فشل في تحديث المعاملة'
      throw e
    } finally {
      loading.value = false
    }
  }

  async function remove(id) {
    loading.value = true
    error.value = null
    try {
      await transactionsApi.delete(id)
      items.value = items.value.filter((i) => i.id !== id)
    } catch (e) {
      error.value = e.response?.data?.detail || 'فشل في حذف المعاملة'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { items, current, loading, error, total, fetchList, fetchOne, create, update, remove }
})
