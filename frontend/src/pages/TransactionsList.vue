<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">المعاملات</h1>
      <router-link to="/newtransaction"
        class="bg-blue-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-800 transition-colors">
        معاملة جديدة
      </router-link>
    </div>
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-4">
      <div class="flex gap-3">
        <input v-model="searchQuery" @input="debouncedSearch" placeholder="بحث..."
          class="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        <select v-model="statusFilter" @change="fetchData"
          class="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500">
          <option value="">جميع الحالات</option>
          <option value="draft">مسودة</option>
          <option value="approved">معتمد</option>
          <option value="rejected">مرفوض</option>
          <option value="archived">مؤرشف</option>
          <option value="cancelled">ملغي</option>
        </select>
      </div>
    </div>
    <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
    <div v-else-if="error" class="bg-red-50 text-red-600 text-sm p-4 rounded-lg">{{ error }}</div>
    <div v-else-if="items.length === 0" class="text-center py-12 text-slate-400">لا توجد معاملات</div>
    <div v-else class="space-y-3">
      <div v-for="tx in items" :key="tx.id" @click="viewTransaction(tx.id)"
        class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 hover:border-blue-300 cursor-pointer transition-colors">
        <div class="flex items-center justify-between">
          <div>
            <div class="font-semibold text-slate-800">{{ tx.transaction_no }}</div>
            <div class="text-sm text-slate-500 mt-1">{{ tx.transaction_type }} - {{ tx.sender_name }} → {{ tx.receiver_name }}</div>
            <div class="text-xs text-slate-400 mt-1">{{ tx.transaction_date }}</div>
          </div>
          <div class="text-left">
            <span :class="statusClass(tx.status)" class="px-2.5 py-1 rounded-full text-xs font-medium">
              {{ statusLabel(tx.status) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { transactionsApi } from '../api'

const router = useRouter()
const items = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const statusFilter = ref('')

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

let debounceTimer = null
function debouncedSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchData, 300)
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (searchQuery.value) params.search = searchQuery.value
    if (statusFilter.value) params.status = statusFilter.value
    const response = await transactionsApi.list(params)
    items.value = response.data
  } catch (e) {
    error.value = 'فشل في تحميل المعاملات'
  } finally {
    loading.value = false
  }
}

function viewTransaction(id) {
  router.push(`/transactiondetails?id=${id}`)
}

onMounted(fetchData)
</script>
