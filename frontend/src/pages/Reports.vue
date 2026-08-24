<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">التقارير</h1>
        <p class="text-sm text-slate-500 mt-1">استعرض الإحصائيات وصدّر بيانات المعاملات حسب الفلاتر المطلوبة.</p>
      </div>
      <div class="flex items-center gap-2 text-xs" :class="loading ? 'text-blue-600' : 'text-slate-400'" aria-live="polite">
        <span v-if="loading" class="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></span>
        {{ loading ? 'جاري تحديث التقرير...' : lastUpdated ? `آخر تحديث: ${formatDateTime(lastUpdated)}` : '' }}
      </div>
    </div>

    <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6" aria-labelledby="filters-title">
      <div class="flex items-center gap-2 mb-4">
        <span class="text-indigo-600" v-html="icons.filter"></span>
        <h2 id="filters-title" class="text-lg font-semibold text-slate-800">فلاتر التقرير</h2>
      </div>
      <form class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4" @submit.prevent="loadReport">
        <div>
          <label class="gov-label" for="start-date">من تاريخ</label>
          <input id="start-date" v-model="filters.start_date" type="date" class="gov-input" />
        </div>
        <div>
          <label class="gov-label" for="end-date">إلى تاريخ</label>
          <input id="end-date" v-model="filters.end_date" type="date" class="gov-input" />
        </div>
        <div>
          <label class="gov-label" for="status-filter">الحالة</label>
          <select id="status-filter" v-model="filters.status" class="gov-select">
            <option value="">كل الحالات</option>
            <option v-for="option in statusOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
          </select>
        </div>
        <div>
          <label class="gov-label" for="type-filter">نوع المعاملة</label>
          <input id="type-filter" v-model.trim="filters.transaction_type" type="text" class="gov-input" placeholder="مثال: استلام" />
        </div>
        <div class="flex items-end gap-2">
          <button type="submit" class="gov-btn-primary flex-1" :disabled="loading">
            <span v-html="icons.search"></span>
            تطبيق
          </button>
          <button type="button" class="gov-btn-secondary" :disabled="loading" @click="resetFilters">مسح</button>
        </div>
      </form>
      <p v-if="filterError" class="text-red-600 text-xs mt-3" role="alert">{{ filterError }}</p>
    </section>

    <div v-if="loading && !report" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <div v-for="i in 4" :key="i" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="skeleton h-4 w-24 mb-3"></div>
        <div class="skeleton h-8 w-16"></div>
      </div>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center justify-between gap-3" role="alert">
      <span>{{ error }}</span>
      <button class="font-medium underline" @click="loadReport">إعادة المحاولة</button>
    </div>

    <template v-else-if="report">
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <div v-for="card in statCards" :key="card.key" class="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">{{ card.label }}</span>
            <span :class="card.color" v-html="card.icon"></span>
          </div>
          <div class="text-3xl font-bold" :class="card.valueColor">{{ card.value }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-5" aria-labelledby="status-report-title">
          <h2 id="status-report-title" class="text-lg font-semibold text-slate-800 mb-4">توزيع الحالات</h2>
          <div class="space-y-3">
            <div v-for="item in statusRows" :key="item.key" class="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
              <span class="flex items-center gap-2 text-sm text-slate-600"><span class="w-2.5 h-2.5 rounded-full" :class="item.dot"></span>{{ item.label }}</span>
              <span class="font-bold text-slate-800">{{ item.count }}</span>
            </div>
            <div v-if="!statusRows.length" class="text-sm text-slate-400 text-center py-5">لا توجد بيانات</div>
          </div>
        </section>

        <section class="xl:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-5" aria-labelledby="type-report-title">
          <h2 id="type-report-title" class="text-lg font-semibold text-slate-800 mb-4">حسب نوع المعاملة</h2>
          <div v-if="typeRows.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="item in typeRows" :key="item.type" class="p-3 bg-slate-50 rounded-lg">
              <div class="flex justify-between gap-3 text-sm mb-2"><span class="truncate text-slate-700" :title="item.type">{{ item.type }}</span><strong>{{ item.count }}</strong></div>
              <div class="h-2 bg-slate-200 rounded-full overflow-hidden"><div class="h-full bg-indigo-500 rounded-full" :style="{ width: `${item.percent}%` }"></div></div>
            </div>
          </div>
          <div v-else class="text-sm text-slate-400 text-center py-8">لا توجد بيانات</div>
        </section>
      </div>

      <section class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden" aria-labelledby="transactions-report-title">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 p-5 border-b border-slate-100">
          <div>
            <h2 id="transactions-report-title" class="text-lg font-semibold text-slate-800">بيانات المعاملات</h2>
            <p class="text-xs text-slate-500 mt-1">{{ report.summary.total }} نتيجة مطابقة للفلاتر الحالية</p>
          </div>
          <div class="flex items-center gap-2">
            <button type="button" class="gov-btn-success" :disabled="exporting !== null" @click="exportReport('excel')">
              <span v-html="icons.download"></span>{{ exporting === 'excel' ? 'جاري التصدير...' : 'Excel' }}
            </button>
            <button type="button" class="gov-btn-danger" :disabled="exporting !== null" @click="exportReport('pdf')">
              <span v-html="icons.download"></span>{{ exporting === 'pdf' ? 'جاري التصدير...' : 'PDF' }}
            </button>
          </div>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm text-right">
            <thead class="bg-slate-50 text-slate-500">
              <tr><th class="px-4 py-3 font-medium">رقم المعاملة</th><th class="px-4 py-3 font-medium">النوع</th><th class="px-4 py-3 font-medium">المرسل</th><th class="px-4 py-3 font-medium">المستلم</th><th class="px-4 py-3 font-medium">الحالة</th><th class="px-4 py-3 font-medium">التاريخ</th></tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr v-for="transaction in report.transactions" :key="transaction.id" class="hover:bg-slate-50">
                <td class="px-4 py-3 font-medium text-primary-900">{{ transaction.transaction_no }}</td><td class="px-4 py-3">{{ transaction.transaction_type }}</td><td class="px-4 py-3">{{ transaction.sender_name }}</td><td class="px-4 py-3">{{ transaction.receiver_name }}</td><td class="px-4 py-3"><span class="gov-badge bg-slate-100 text-slate-700">{{ statusLabel(transaction.status) }}</span></td><td class="px-4 py-3 whitespace-nowrap">{{ transaction.transaction_date }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="!report.transactions.length" class="text-center py-12 text-slate-400 text-sm">لا توجد معاملات مطابقة للفلاتر الحالية</div>
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

const icons = ICONS
const loading = ref(true)
const exporting = ref(null)
const error = ref(null)
const filterError = ref(null)
const lastUpdated = ref(null)
const report = ref(null)
const filters = ref({ start_date: '', end_date: '', status: '', transaction_type: '' })
const statusOptions = [
  { value: 'approved', label: 'معتمدة' },
  { value: 'draft', label: 'مسودة' },
  { value: 'rejected', label: 'مرفوضة' },
  { value: 'archived', label: 'مؤرشفة' },
  { value: 'cancelled', label: 'ملغاة' },
]
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
    filterError.value = 'تاريخ البداية يجب أن يسبق تاريخ النهاية'
    return
  }
  loading.value = true
  error.value = null
  try {
    const response = await reportsApi.summary(cleanParams())
    report.value = response.data
    lastUpdated.value = new Date()
  } catch (e) {
    error.value = e.apiMessage || e.response?.data?.message || e.response?.data?.detail || 'تعذر تحميل التقرير'
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
    const response = format === 'excel' ? await reportsApi.exportExcel(cleanParams()) : await reportsApi.exportPdf(cleanParams())
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
    error.value = e.apiMessage || e.response?.data?.message || 'تعذر تصدير التقرير'
  } finally {
    exporting.value = null
  }
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat('ar-IQ', { dateStyle: 'medium', timeStyle: 'short' }).format(value)
}

onMounted(loadReport)
</script>
