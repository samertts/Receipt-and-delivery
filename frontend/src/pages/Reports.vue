<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">التقارير</h1>
    <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-semibold mb-4">ملخص المعاملات</h2>
        <div class="space-y-3">
          <div class="flex justify-between text-sm">
            <span class="text-slate-500">إجمالي المعاملات</span>
            <span class="font-semibold">{{ stats.total }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-slate-500">معتمدة</span>
            <span class="font-semibold text-emerald-600">{{ stats.approved }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-slate-500">مسودة</span>
            <span class="font-semibold text-amber-600">{{ stats.draft }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-slate-500">مرفوضة</span>
            <span class="font-semibold text-red-600">{{ stats.rejected }}</span>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-semibold mb-4">حسب نوع المعاملة</h2>
        <div v-if="byType.length === 0" class="text-sm text-slate-400">لا توجد بيانات</div>
        <div v-else class="space-y-2">
          <div v-for="t in byType" :key="t.type" class="flex justify-between text-sm">
            <span>{{ t.type }}</span>
            <span class="font-semibold">{{ t.count }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { transactionsApi } from '../api'

const loading = ref(true)
const stats = ref({ total: 0, approved: 0, draft: 0, rejected: 0 })
const byType = ref([])

onMounted(async () => {
  try {
    const res = await transactionsApi.list({ limit: 1000 })
    const txns = res.data
    stats.value = {
      total: txns.length,
      approved: txns.filter((t) => t.status === 'approved').length,
      draft: txns.filter((t) => t.status === 'draft').length,
      rejected: txns.filter((t) => t.status === 'rejected').length,
    }
    const typeMap = {}
    txns.forEach((t) => {
      typeMap[t.transaction_type] = (typeMap[t.transaction_type] || 0) + 1
    })
    byType.value = Object.entries(typeMap).map(([type, count]) => ({ type, count }))
  } catch (e) {
    // ignore
  } finally {
    loading.value = false
  }
})
</script>
