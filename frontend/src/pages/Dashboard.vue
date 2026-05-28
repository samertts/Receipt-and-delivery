<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">لوحة التحكم</h1>
    <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="text-sm text-slate-500 mb-1">إجمالي المعاملات</div>
          <div class="text-3xl font-bold text-blue-900">{{ stats.totalTransactions }}</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="text-sm text-slate-500 mb-1">معتمدة</div>
          <div class="text-3xl font-bold text-emerald-600">{{ stats.approved }}</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="text-sm text-slate-500 mb-1">مسودة</div>
          <div class="text-3xl font-bold text-amber-600">{{ stats.draft }}</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="text-sm text-slate-500 mb-1">المؤسسات</div>
          <div class="text-3xl font-bold text-slate-700">{{ stats.totalOrganizations }}</div>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">آخر المعاملات</h2>
        <div v-if="recentTransactions.length === 0" class="text-center py-8 text-slate-400">
          لا توجد معاملات بعد
        </div>
        <div v-else class="space-y-3">
          <div v-for="tx in recentTransactions" :key="tx.id"
            class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
            <div>
              <div class="font-medium text-slate-800">{{ tx.transaction_no }}</div>
              <div class="text-sm text-slate-500">{{ tx.transaction_type }} - {{ tx.sender_name }}</div>
            </div>
            <span :class="statusClass(tx.status)" class="px-2.5 py-1 rounded-full text-xs font-medium">
              {{ statusLabel(tx.status) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="error" class="bg-red-50 text-red-600 text-sm p-4 rounded-lg mt-4">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { transactionsApi, organizationsApi } from '../api'

const loading = ref(true)
const error = ref(null)
const stats = ref({ totalTransactions: 0, approved: 0, draft: 0, totalOrganizations: 0 })
const recentTransactions = ref([])

function statusLabel(status) {
  const labels = { draft: 'مسودة', approved: 'معتمد', rejected: 'مرفوض', archived: 'مؤرشف', cancelled: 'ملغي' }
  return labels[status] || status
}

function statusClass(status) {
  const classes = {
    draft: 'bg-amber-50 text-amber-700',
    approved: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-700',
    archived: 'bg-slate-100 text-slate-600',
    cancelled: 'bg-slate-100 text-slate-600',
  }
  return classes[status] || 'bg-slate-100 text-slate-600'
}

onMounted(async () => {
  try {
    const [txRes, orgRes] = await Promise.all([
      transactionsApi.list({ limit: 5 }),
      organizationsApi.list({}),
    ])
    recentTransactions.value = txRes.data
    stats.value.totalTransactions = txRes.data.length
    stats.value.approved = txRes.data.filter((t) => t.status === 'approved').length
    stats.value.draft = txRes.data.filter((t) => t.status === 'draft').length
    stats.value.totalOrganizations = orgRes.data.length
  } catch (e) {
    error.value = 'فشل في تحميل البيانات'
  } finally {
    loading.value = false
  }
})
</script>
