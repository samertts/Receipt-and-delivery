<template>
  <div class="reports-page space-y-6 pb-8">
    <header class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
      <div>
        <h1 class="page-title">{{ L.reports.title }}</h1>
        <p class="page-subtitle">{{ L.reports.description }}</p>
      </div>
      <div class="status-strip" :class="loading ? 'text-blue-700' : 'text-slate-600'" aria-live="polite" aria-atomic="true">
        <span v-if="loading" class="w-2 h-2 rounded-full bg-blue-500 animate-pulse" aria-hidden="true"></span>
        <span>{{ loading ? L.reports.updating : lastUpdated ? `${L.reports.lastUpdated}: ${formatDateTime(lastUpdated)}` : L.reports.noData }}</span>
      </div>
    </header>

    <section class="gov-card report-filter-card p-5" aria-labelledby="filters-title">
      <div class="report-section-heading">
        <span class="text-blue-700" v-html="icons.filter" aria-hidden="true"></span>
        <div>
          <h2 id="filters-title" class="text-lg font-semibold text-slate-800">{{ L.reports.filters }}</h2>
          <p class="page-subtitle">{{ L.reports.description }}</p>
        </div>
      </div>
      <form class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4" @submit.prevent="loadReport">
        <div>
          <label class="gov-label" for="start-date">{{ L.reports.startDate }}</label>
          <input id="start-date" v-model="filters.start_date" type="date" class="gov-input" />
        </div>
        <div>
          <label class="gov-label" for="end-date">{{ L.reports.endDate }}</label>
          <input id="end-date" v-model="filters.end_date" type="date" class="gov-input" />
        </div>
        <div>
          <label class="gov-label" for="status-filter">{{ L.settings.status }}</label>
          <select id="status-filter" v-model="filters.status" class="gov-select">
            <option value="">{{ L.reports.allStatuses }}</option>
            <option v-for="option in statusOptions" :key="option" :value="option">{{ L.status[option] }}</option>
          </select>
        </div>
        <div>
          <label class="gov-label" for="type-filter">{{ L.form.transactionType }}</label>
          <input id="type-filter" v-model.trim="filters.transaction_type" type="text" class="gov-input" :placeholder="L.reports.transactionTypePlaceholder" />
        </div>
        <div class="flex items-end gap-2">
          <button type="submit" class="gov-btn-primary flex-1" :disabled="loading" :aria-busy="loading">
            <span v-html="icons.search" aria-hidden="true"></span>
            {{ L.reports.apply }}
          </button>
          <button type="button" class="gov-btn-secondary" :disabled="loading" @click="resetFilters">{{ L.reports.reset }}</button>
        </div>
      </form>
      <p v-if="filterError" class="text-red-600 text-xs mt-3" role="alert">{{ filterError }}</p>
    </section>

    <div v-if="loading && !report" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4" role="status" aria-live="polite" :aria-label="L.actions.loading">
      <div v-for="i in 4" :key="i" class="gov-card report-kpi-card p-5">
        <div class="skeleton h-4 w-24 mb-3"></div>
        <div class="skeleton h-8 w-16"></div>
      </div>
    </div>

    <div v-else-if="error" class="status-strip status-strip--error justify-between gap-3" role="alert">
      <span>{{ error }}</span>
      <button class="gov-btn-secondary" @click="loadReport">{{ L.actions.retry }}</button>
    </div>

    <template v-else-if="report">
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4" :aria-label="L.reports.summary">
        <div v-for="card in statCards" :key="card.key" class="gov-card report-kpi-card p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">{{ card.label }}</span>
            <span :class="card.color" v-html="card.icon" aria-hidden="true"></span>
          </div>
          <div class="text-3xl font-bold" :class="card.valueColor">{{ card.value }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <section class="gov-card report-panel p-5" aria-labelledby="status-report-title">
          <h2 id="status-report-title" class="text-lg font-semibold text-slate-800 mb-4">{{ L.reports.statusDistribution }}</h2>
          <div class="space-y-3">
            <div v-for="item in statusRows" :key="item.key" class="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <span class="flex items-center gap-2 text-sm text-slate-600"><span class="w-2.5 h-2.5 rounded-full" :class="item.dot"></span>{{ item.label }}</span>
              <span class="font-bold text-slate-800">{{ item.count }}</span>
            </div>
            <div v-if="!statusRows.length" class="text-sm text-slate-400 text-center py-5">لا توجد بيانات</div>
          </div>
        </section>

        <section class="gov-card report-panel xl:col-span-2 p-5" aria-labelledby="type-report-title">
          <h2 id="type-report-title" class="text-lg font-semibold text-slate-800 mb-4">{{ L.reports.byType }}</h2>
          <div v-if="typeRows.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="item in typeRows" :key="item.type" class="report-type-row p-3 rounded-lg">
                <div class="flex justify-between gap-3 text-sm mb-2"><span class="truncate text-slate-700" :title="item.type">{{ item.type }}</span><strong class="tabular-nums">{{ item.count }}</strong></div>
                <div class="h-2 bg-slate-200 rounded-full overflow-hidden" role="progressbar" :aria-valuenow="item.percent" aria-valuemin="0" aria-valuemax="100" :aria-label="`${item.type}: ${item.percent}%`"><div class="h-full bg-blue-600 rounded-full" :style="{ width: `${item.percent}%` }"></div></div>

            </div>
          </div>
          <div v-else class="text-sm text-slate-400 text-center py-8">لا توجد بيانات</div>
        </section>
      </div>

      <section class="gov-card report-table-panel overflow-hidden" aria-labelledby="transactions-report-title">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-5 border-b border-slate-100">
          <div>
            <h2 id="transactions-report-title" class="text-lg font-semibold text-slate-800">{{ L.reports.transactionData }}</h2>
            <p class="text-xs text-slate-500 mt-1">{{ report.summary.total }} {{ L.reports.matchingResults }}</p>
          </div>
          <div class="report-export-actions flex items-center gap-2">
            <button type="button" class="gov-btn-success" :disabled="exporting !== null" @click="exportReport('excel')">
              <span v-html="icons.download" aria-hidden="true"></span>{{ exporting === 'excel' ? L.reports.exporting : L.reports.exportExcel }}
            </button>
            <button type="button" class="gov-btn-danger" :disabled="exporting !== null" @click="exportReport('pdf')">
              <span v-html="icons.download" aria-hidden="true"></span>{{ exporting === 'pdf' ? L.reports.exporting : L.reports.exportPdf }}
            </button>
          </div>
        </div>
        <div class="overflow-x-auto" tabindex="0" aria-label="{{ L.reports.transactionData }}">
          <table class="w-full text-sm text-right report-table">
            <caption class="sr-only">{{ L.reports.transactionData }}</caption>
            <thead class="bg-slate-50 text-slate-500">
              <tr><th class="px-4 py-3 font-medium">{{ L.tx.title }}</th><th class="px-4 py-3 font-medium">{{ L.form.transactionType }}</th><th class="px-4 py-3 font-medium">{{ L.form.sender }}</th><th class="px-4 py-3 font-medium">{{ L.form.receiver }}</th><th class="px-4 py-3 font-medium">{{ L.settings.status }}</th><th class="px-4 py-3 font-medium">{{ L.form.transactionDate }}</th></tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="transaction in report.transactions" :key="transaction.id" class="hover:bg-slate-50 transition-colors duration-200">
                <td class="px-4 py-3 font-medium text-primary-900">{{ transaction.transaction_no }}</td><td class="px-4 py-3">{{ transaction.transaction_type }}</td><td class="px-4 py-3">{{ transaction.sender_name }}</td><td class="px-4 py-3">{{ transaction.receiver_name }}</td><td class="px-4 py-3"><span class="gov-badge bg-slate-100 text-slate-700">{{ statusLabel(transaction.status) }}</span></td><td class="px-4 py-3 whitespace-nowrap">{{ transaction.transaction_date }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!report.transactions.length" class="text-center py-12 text-slate-400 text-sm">{{ L.reports.noMatching }}</div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { reportsApi } from '../api'
import { ICONS } from '../composables/useIcons'
import { statusLabel } from '../composables/useStatus'
import { L, useLocale } from '../composables/useLocale'

const icons = ICONS
const { locale } = useLocale()
const loading = ref(true)
const exporting = ref(null)
const error = ref(null)
const filterError = ref(null)
const lastUpdated = ref(null)
const report = ref(null)
const filters = ref({ start_date: '', end_date: '', status: '', transaction_type: '' })
const statusOptions = ['approved', 'draft', 'rejected', 'archived', 'cancelled']
const statusMeta = {
  approved: { dot: 'bg-emerald-500', color: 'text-emerald-600', valueColor: 'text-emerald-600', icon: ICONS.check },
  draft: { dot: 'bg-amber-500', color: 'text-amber-600', valueColor: 'text-amber-600', icon: ICONS.edit },
  rejected: { dot: 'bg-red-500', color: 'text-red-600', valueColor: 'text-red-600', icon: ICONS.alert },
  archived: { dot: 'bg-slate-500', color: 'text-slate-600', valueColor: 'text-slate-600', icon: ICONS.archive },
  cancelled: { dot: 'bg-slate-400', color: 'text-slate-500', valueColor: 'text-slate-500', icon: ICONS.close || ICONS.alert },
}

const statCards = computed(() => {
  const byStatus = report.value?.summary?.by_status || {}
  return [
    { key: 'total', label: 'إجمالي المعاملات', value: report.value?.summary?.total || 0, color: 'text-blue-600', valueColor: 'text-primary-900', icon: icons.transactions },
    ...['approved', 'draft', 'rejected'].map((key) => ({ key, label: statusLabel(key), value: byStatus[key] || 0, ...statusMeta[key] })),
  ]
})
const statusRows = computed(() => Object.entries(report.value?.summary?.by_status || {}).map(([key, count]) => ({ key, count, label: statusLabel(key), ...(statusMeta[key] || { dot: 'bg-slate-400' }) })).filter((item) => item.count > 0))
const typeRows = computed(() => {
  const values = Object.entries(report.value?.summary?.by_type || {}).map(([type, count]) => ({ type, count }))
  const max = Math.max(...values.map((item) => item.count), 1)
  return values.sort((a, b) => b.count - a.count).map((item) => ({ ...item, percent: Math.round((item.count / max) * 100) }))
})

function cleanParams() {
  return Object.fromEntries(Object.entries(filters.value).filter(([, value]) => value))
}

async function loadReport() {
  filterError.value = null
  if (filters.value.start_date && filters.value.end_date && filters.value.start_date > filters.value.end_date) {
    filterError.value = L.reports.invalidDates
    return
  }
  loading.value = true
  error.value = null
  try {
    const response = await reportsApi.summary({ ...cleanParams(), lang: locale.value })
    report.value = response.data
    lastUpdated.value = new Date()
  } catch (e) {
    error.value = e.apiMessage || e.response?.data?.message || e.response?.data?.detail || L.reports.loadFailed
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value = { start_date: '', end_date: '', status: '', transaction_type: '' }
  loadReport()
}

async function exportReport(format) {
  exporting.value = format
  try {
    const response = format === 'excel' ? await reportsApi.exportExcel({ ...cleanParams(), lang: locale.value }) : await reportsApi.exportPdf({ ...cleanParams(), lang: locale.value })
    const blob = response.data instanceof Blob ? response.data : new Blob([response.data])
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `transactions_report.${format === 'excel' ? 'xlsx' : 'pdf'}`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e.apiMessage || e.response?.data?.message || L.reports.exportFailed
  } finally {
    exporting.value = null
  }
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat('ar-IQ', { dateStyle: 'medium', timeStyle: 'short' }).format(value)
}

onMounted(loadReport)
</script>
