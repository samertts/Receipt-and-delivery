<template>
  <div class="transactions-page space-y-6 pb-8">
    <header class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
      <div>
        <h1 class="page-title">{{ L.tx.title }}</h1>
        <p class="page-subtitle">{{ L.tx.description }}</p>
      </div>
      <router-link to="/newtransaction" class="gov-btn-primary">
        <span v-html="ICONS.plus" aria-hidden="true"></span>
        {{ L.nav.newTransaction }}
      </router-link>
    </header>

    <section class="gov-card transactions-filter-card p-5 space-y-4" aria-labelledby="transaction-filters-title">
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
        <div>
          <h2 id="transaction-filters-title" class="text-lg font-semibold text-slate-800">{{ L.actions.search }}</h2>
          <p class="page-subtitle">{{ L.tx.description }}</p>
        </div>
        <span v-if="loading" class="status-strip text-blue-700" role="status" aria-live="polite">{{ L.actions.loading }}</span>
      </div>
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <label for="transaction-search" class="sr-only">{{ L.actions.search }}</label>
          <span class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" v-html="ICONS.search" aria-hidden="true"></span>
          <input
            id="transaction-search"
            v-model="searchQuery"
            @input="debouncedSearch"
            :placeholder="L.tx.searchPlaceholder"
            :aria-label="L.tx.searchPlaceholder"
            class="gov-input pr-10"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''; debouncedSearch()"
            class="gov-btn-icon absolute left-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
            :aria-label="L.actions.clear"
          >
            <span v-html="ICONS.close" aria-hidden="true"></span>
          </button>
        </div>
        <label class="sr-only" for="transaction-status">{{ L.settings.status }}</label>
        <select id="transaction-status" v-model="statusFilter" @change="fetchData" class="gov-select sm:w-40">
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
          <label class="gov-label shrink-0 mb-0" for="date-from">{{ L.tx.from }}</label>
          <input id="date-from" v-model="dateFrom" type="date" @change="fetchData" class="gov-input text-sm" />
        </div>
        <div class="flex items-center gap-2">
          <label class="gov-label shrink-0 mb-0" for="date-to">{{ L.tx.to }}</label>
          <input id="date-to" v-model="dateTo" type="date" @change="fetchData" class="gov-input text-sm" />
        </div>
        <button
          v-if="hasActiveFilters"
          @click="clearFilters"
          class="gov-btn-secondary"
        >
          <span v-html="ICONS.close" aria-hidden="true"></span>
          {{ L.actions.clear }}
        </button>
      </div>
    </section>

    <div v-if="loading" role="status" aria-live="polite" :aria-label="L.actions.loading">
      <div class="space-y-3">
        <div v-for="i in 3" :key="i" class="gov-card p-4">
          <div class="skeleton h-5 w-48 mb-2"></div>
          <div class="skeleton h-4 w-72 mb-2"></div>
          <div class="skeleton h-3 w-32"></div>
        </div>
      </div>
    </div>

    <div v-else-if="error" role="alert" class="status-strip status-strip--error justify-between gap-3">
      <span v-html="ICONS.alert" class="shrink-0" aria-hidden="true"></span>
      <span>{{ error }}</span>
      <button @click="fetchData" class="gov-btn-secondary">{{ L.actions.retry }}</button>
    </div>

    <div v-else-if="items.length === 0" class="gov-card text-center py-16" role="status" aria-live="polite">
      <div class="text-slate-300 text-5xl mb-4" v-html="ICONS.doc" aria-hidden="true"></div>
      <p class="text-slate-500 text-sm">{{ hasActiveFilters ? L.actions.noResults : L.tx.noTransactions }}</p>
      <button v-if="hasActiveFilters" @click="clearFilters" class="gov-btn-secondary mt-4">
        {{ L.actions.clear }}
      </button>
    </div>

    <div v-else class="space-y-3" aria-live="polite">
      <div class="transactions-result-bar" role="status">
        <span class="font-semibold text-slate-800">{{ L.tx.total }} {{ total }} {{ L.tx.transaction }}</span>
      </div>
      <div
        v-for="tx in items" :key="tx.id"
        v-memo="[tx.status, tx.transaction_no]"
        @click="viewTransaction(tx.id)"
        @keydown.enter="viewTransaction(tx.id)"
        @keydown.space.prevent="viewTransaction(tx.id)"
        class="gov-card transaction-list-card p-4 hover:border-blue-300 hover:shadow-md transition-colors duration-200"
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
              <span v-html="ICONS.calendar" aria-hidden="true"></span>
              {{ tx.transaction_date }}
            </div>
          </div>
          <div class="text-slate-300 mr-4">
            <span v-html="ICONS.arrowLeft" aria-hidden="true"></span>
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
          class="gov-btn-secondary"
          :aria-label="L.tx.previous"
        >
          {{ L.tx.previous }}
        </button>
        <span class="px-3 py-1.5 text-slate-600 tabular-nums" aria-live="polite">{{ page }} / {{ totalPages }}</span>
        <button
          :disabled="page >= totalPages"
          @click="nextPage"
          class="gov-btn-secondary"
          :aria-label="L.tx.next"
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
