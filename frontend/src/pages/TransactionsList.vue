<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <h1 class="text-2xl font-bold text-slate-800">{{ L.tx.title }}</h1>
      <router-link to="/newtransaction" class="gov-btn-primary">
        <span v-html="ICONS.plus"></span>
        {{ L.nav.newTransaction }}
      </router-link>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-4 space-y-3">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <span class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" v-html="ICONS.search"></span>
          <input
            v-model="searchQuery"
            @input="debouncedSearch"
            :placeholder="L.tx.searchPlaceholder"
            class="gov-input pr-10"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''; debouncedSearch()"
            class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            :aria-label="L.actions.clear"
          >
            <span v-html="ICONS.close"></span>
          </button>
        </div>
        <select v-model="statusFilter" @change="fetchData" class="gov-select sm:w-40">
          <option value="">{{ L.tx.allStatus }}</option>
          <option value="draft">{{ L.status.draft }}</option>
          <option value="approved">{{ L.status.approved }}</option>
          <option value="rejected">{{ L.status.rejected }}</option>
          <option value="archived">{{ L.status.archived }}</option>
          <option value="cancelled">{{ L.status.cancelled }}</option>
        </select>
      </div>
      <div class="flex flex-col sm:flex-row gap-3 text-sm">
        <div class="flex items-center gap-2">
          <span class="text-slate-500 shrink-0">{{ L.tx.from }}:</span>
          <input v-model="dateFrom" type="date" @change="fetchData" class="gov-input text-sm" />
        </div>
        <div class="flex items-center gap-2">
          <span class="text-slate-500 shrink-0">{{ L.tx.to }}:</span>
          <input v-model="dateTo" type="date" @change="fetchData" class="gov-input text-sm" />
        </div>
        <button
          v-if="hasActiveFilters"
          @click="clearFilters"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center gap-1"
        >
          <span v-html="ICONS.close"></span>
          {{ L.actions.clear }}
        </button>
      </div>
    </div>

    <div v-if="loading" role="status" aria-live="polite" aria-label="تحميل المعاملات">
      <div class="space-y-3">
        <div v-for="i in 3" :key="i" class="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <div class="skeleton h-5 w-48 mb-2"></div>
          <div class="skeleton h-4 w-72 mb-2"></div>
          <div class="skeleton h-3 w-32"></div>
        </div>
      </div>
    </div>

    <div v-else-if="error" role="alert" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
      <span v-html="ICONS.alert" class="shrink-0"></span>
      <span>{{ error }}</span>
      <button @click="fetchData" class="mr-auto text-red-600 hover:text-red-800 font-medium">{{ L.actions.retry }}</button>
    </div>

    <div v-else-if="items.length === 0" class="text-center py-16 bg-white rounded-xl shadow-sm border border-slate-200" role="status" aria-live="polite">
      <div class="text-slate-300 text-5xl mb-4" v-html="ICONS.doc"></div>
      <p class="text-slate-500 text-sm">{{ hasActiveFilters ? L.actions.noResults : L.tx.noTransactions }}</p>
      <button v-if="hasActiveFilters" @click="clearFilters" class="gov-btn-secondary mt-4">
        {{ L.actions.clear }}
      </button>
    </div>

    <div v-else class="space-y-2" role="status" aria-live="polite">
      <div
        v-for="tx in items" :key="tx.id"
        v-memo="[tx.status, tx.transaction_no]"
        @click="viewTransaction(tx.id)"
        @keydown.enter="viewTransaction(tx.id)"
        @keydown.space.prevent="viewTransaction(tx.id)"
        class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 hover:border-blue-300 hover:shadow-md cursor-pointer transition-all"
        tabindex="0" role="button"
        :aria-label="`${L.tx.transaction} ${tx.transaction_no} — ${statusLabel(tx.status)}`"
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
              <span v-html="ICONS.calendar"></span>
              {{ tx.transaction_date }}
            </div>
          </div>
          <div class="text-slate-300 mr-4">
            <span v-html="ICONS.arrowLeft"></span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="items.length > 0" class="flex items-center justify-between mt-4 text-sm text-slate-500">
      <span>{{ L.tx.total }} {{ total }} {{ L.tx.transaction }}</span>
      <div class="flex gap-2 items-center">
        <button
          :disabled="page <= 1"
          @click="prevPage"
          class="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-slate-50 transition-colors"
        >
          {{ L.tx.previous }}
        </button>
        <span class="px-3 py-1.5 text-slate-600">{{ page }} / {{ totalPages }}</span>
        <button
          :disabled="page >= totalPages"
          @click="nextPage"
          class="px-3 py-1.5 border rounded-lg disabled:opacity-40 hover:bg-slate-50 transition-colors"
        >
          {{ L.tx.next }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, shallowRef, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTransactionStore } from '../stores/transactions'
import { statusLabel, statusClass } from '../composables/useStatus'
import { ICONS } from '../composables/useIcons'
import { L } from '../composables/useLocale'

const router = useRouter()
const store = useTransactionStore()

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
    error.value = L.errors.loadFailedTx
  } finally {
    loading.value = false
  }
}

function viewTransaction(id) {
  router.push(`/transactiondetails?id=${id}`)
}

onMounted(fetchData)
</script>
