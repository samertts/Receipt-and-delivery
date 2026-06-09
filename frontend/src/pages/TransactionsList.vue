<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <h1 class="text-2xl font-bold text-slate-800">المعاملات</h1>
      <router-link to="/newtransaction" class="gov-btn-primary">
        <span v-html="icons.plus"></span>
        معاملة جديدة
      </router-link>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-4 space-y-3">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <span class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" v-html="icons.search"></span>
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            placeholder="بحث برقم المعاملة أو اسم المرسل..."
            class="gov-input pr-10"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''; debouncedSearch()"
            class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            aria-label="مسح البحث"
          >
            <span v-html="icons.close"></span>
          </button>
        </div>
        <select v-model="statusFilter" @change="fetchData" class="gov-select sm:w-40">
          <option value="">جميع الحالات</option>
          <option value="draft">مسودة</option>
          <option value="approved">معتمد</option>
          <option value="rejected">مرفوض</option>
          <option value="archived">مؤرشف</option>
          <option value="cancelled">ملغي</option>
        </select>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 text-sm">
        <div class="flex items-center gap-2">
          <span class="text-slate-500 shrink-0">من:</span>
          <input v-model="dateFrom" type="date" @change="fetchData" class="gov-input text-sm" />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-slate-500 shrink-0">إلى:</span>
          <input v-model="dateTo" type="date" @change="fetchData" class="gov-input text-sm" />
        </div>
        <button
          v-if="hasActiveFilters"
          @click="clearFilters"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
        >
          <span v-html="icons.close"></span>
          مسح الفلاتر
        </button>
      </div>
    </div>

    <div v-if="loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div class="skeleton h-5 w-48 mb-2"></div>
        <div class="skeleton h-4 w-72 mb-2"></div>
        <div class="skeleton h-3 w-32"></div>
      </div>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
      <span v-html="icons.alert"></span>
      <span>{{ error }}</span>
      <button @click="fetchData" class="mr-auto text-red-600 hover:text-red-800 font-medium">إعادة المحاولة</button>
    </div>

    <div v-else-if="items.length === 0" class="text-center py-16 bg-white rounded-xl shadow-sm border border-slate-200">
      <div class="text-slate-300 text-5xl mb-4" v-html="icons.doc"></div>
      <p class="text-slate-500 text-sm">لا توجد معاملات تطابق معايير البحث</p>
      <button v-if="hasActiveFilters" @click="clearFilters" class="gov-btn-secondary mt-4">
        مسح الفلاتر
      </button>
    </div>

    <div v-else class="space-y-2">
      <div
        v-for="tx in items" :key="tx.id"
        @click="viewTransaction(tx.id)"
        class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 hover:border-blue-300 hover:shadow-md cursor-pointer transition-all"
      >
        <div class="flex items-center justify-between">
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <span class="font-semibold text-slate-800">{{ tx.transaction_no }}</span>
              <span :class="statusClass(tx.status)" class="gov-badge">{{ statusLabel(tx.status) }}</span>
            </div>
            <div class="text-sm text-slate-500 mt-1">
              {{ tx.transaction_type }} —
              <span class="font-medium text-slate-600">{{ tx.sender_name }}</span>
              <span class="mx-1 text-slate-300">→</span>
              <span class="font-medium text-slate-600">{{ tx.receiver_name }}</span>
            </div>
            <div class="text-xs text-slate-400 mt-1 flex items-center gap-1">
              <span v-html="icons.calendar"></span>
              {{ tx.transaction_date }}
            </div>
          </div>
          <div class="text-slate-300 mr-4">
            <span v-html="icons.arrowLeft"></span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="items.length > 0" class="flex items-center justify-between mt-4 text-sm text-slate-500">
      <span>إجمالي {{ total }} معاملة</span>
      <div class="flex gap-2 items-center">
        <button
          :disabled="page <= 1"
          @click="prevPage"
          class="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-slate-50 transition-colors"
        >
          السابق
        </button>
        <span class="px-3 py-1.5 text-slate-600">{{ page }} / {{ totalPages }}</span>
        <button
          :disabled="page >= totalPages"
          @click="nextPage"
          class="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-slate-50 transition-colors"
        >
          التالي
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTransactionStore } from '../stores/transactions'
import { statusLabel, statusClass } from '../composables/useStatus'
import { ICONS } from '../composables/useIcons'

const router = useRouter()
const store = useTransactionStore()
const icons = ICONS

const items = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const statusFilter = ref('')
const dateFrom = ref('')
const dateTo = ref('')
const page = ref(1)
const total = ref(0)
const limit = 20

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit)))
const hasActiveFilters = computed(() => searchQuery.value || statusFilter.value || dateFrom.value || dateTo.value)

const DOC_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`
icons.doc = DOC_ICON

let debounceTimer = null
function debouncedSearch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => { page.value = 1; fetchData() }, 300)
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  page.value = 1
  fetchData()
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
    if (dateFrom.value) params.date_from = dateFrom.value
    if (dateTo.value) params.date_to = dateTo.value
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
