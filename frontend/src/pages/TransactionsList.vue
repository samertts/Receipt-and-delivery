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
    <div v-else>
      <div class="space-y-3">
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
      <div class="flex items-center justify-between mt-6 text-sm text-slate-500">
        <span>إجمالي {{ total }} معاملة</span>
        <div class="flex gap-2">
          <button :disabled="page <= 1" @click="prevPage"
            class="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-slate-50">السابق</button>
          <span class="px-3 py-1.5">{{ page }} / {{ totalPages }}</span>
          <button :disabled="page >= totalPages" @click="nextPage"
            class="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-slate-50">التالي</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTransactionStore } from '../stores/transactions'

const router = useRouter()
const store = useTransactionStore()
const items = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const statusFilter = ref('')
const page = ref(1)
const total = ref(0)
const limit = 20

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))

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
  debounceTimer = setTimeout(() => { page.value = 1; fetchData() }, 300)
}

function prevPage() {
  if (page.value <= 1) return
  page.value--
  fetchData()
}

function nextPage() {
  if (page.value >= totalPages.value) return
  page.value++
  fetchData()
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const params = { page: page.value, limit }
    if (searchQuery.value) params.search = searchQuery.value
    if (statusFilter.value) params.status = statusFilter.value
    await store.fetchList(params)
    items.value = store.items
    total.value = store.total
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
