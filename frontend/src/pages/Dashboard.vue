<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-800">{{ L.dashboard.welcome }}, {{ auth.user?.username || L.roles.user }}</h1>
      <p class="text-sm text-slate-500 mt-1">{{ L.dashboard.subtitle }}</p>
    </div>

    <div v-if="loading" role="status" aria-live="polite" :aria-label="L.actions.loading">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div v-for="i in 4" :key="i" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="skeleton h-4 w-24 mb-3"></div>
          <div class="skeleton h-8 w-16"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="skeleton h-5 w-32 mb-4"></div>
        <div v-for="i in 3" :key="i" class="skeleton h-12 w-full mb-2"></div>
      </div>
    </div>

    <div v-else-if="error" role="alert" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
      <span v-html="ICONS.alert" class="shrink-0"></span>
      <span>{{ error }}</span>
      <button @click="loadData" class="mr-auto text-red-600 hover:text-red-800 font-medium">{{ L.actions.retry }}</button>
    </div>

    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div
          class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
          tabindex="0" role="button"
          :aria-label="`${L.dashboard.totalTransactions}: ${stats.totalTransactions}`"
          @click="router.push('/transactionslist')"
          @keydown.enter="router.push('/transactionslist')"
          @keydown.space.prevent="router.push('/transactionslist')"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">{{ L.dashboard.totalTransactions }}</span>
            <span class="text-blue-600" v-html="ICONS.transactions"></span>
          </div>
          <div class="text-3xl font-bold text-primary-900">{{ stats.totalTransactions }}</div>
          <div class="flex items-center gap-1 mt-1">
            <span v-html="trends.total >= 0 ? ICONS.trendUp : ICONS.trendDown" class="w-4 h-4" :class="trends.total >= 0 ? 'text-emerald-500' : 'text-red-500'"></span>
            <span class="text-xs font-medium" :class="trends.total >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ Math.abs(trends.total) }}%</span>
            <span class="text-xs text-slate-400">{{ L.dashboard.monthly }}</span>
          </div>
        </div>

        <div
          class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
          tabindex="0" role="button"
          :aria-label="`${L.dashboard.approved}: ${stats.approved}`"
          @click="router.push('/transactionslist?status=approved')"
          @keydown.enter="router.push('/transactionslist?status=approved')"
          @keydown.space.prevent="router.push('/transactionslist?status=approved')"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">{{ L.dashboard.approved }}</span>
            <span class="text-emerald-600" v-html="ICONS.check"></span>
          </div>
          <div class="text-3xl font-bold text-emerald-600">{{ stats.approved }}</div>
          <div class="flex items-center gap-1 mt-1">
            <span v-html="trends.approved >= 0 ? ICONS.trendUp : ICONS.trendDown" class="w-4 h-4" :class="trends.approved >= 0 ? 'text-emerald-500' : 'text-red-500'"></span>
            <span class="text-xs font-medium" :class="trends.approved >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ Math.abs(trends.approved) }}%</span>
            <span class="text-xs text-slate-400">{{ L.dashboard.monthly }}</span>
          </div>
        </div>

        <div
          class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
          tabindex="0" role="button"
          :aria-label="`${L.dashboard.draft}: ${stats.draft}`"
          @click="router.push('/transactionslist?status=draft')"
          @keydown.enter="router.push('/transactionslist?status=draft')"
          @keydown.space.prevent="router.push('/transactionslist?status=draft')"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">{{ L.dashboard.draft }}</span>
            <span class="text-amber-600" v-html="ICONS.edit"></span>
          </div>
          <div class="text-3xl font-bold text-amber-600">{{ stats.draft }}</div>
          <div class="flex items-center gap-1 mt-1">
            <span v-html="trends.draft >= 0 ? ICONS.trendUp : ICONS.trendDown" class="w-4 h-4" :class="trends.draft >= 0 ? 'text-emerald-500' : 'text-red-500'"></span>
            <span class="text-xs font-medium" :class="trends.draft >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ Math.abs(trends.draft) }}%</span>
            <span class="text-xs text-slate-400">{{ L.dashboard.monthly }}</span>
          </div>
        </div>

        <div
          class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow cursor-pointer"
          tabindex="0" role="button"
          :aria-label="`${L.dashboard.organizations}: ${stats.totalOrganizations}`"
          @click="router.push('/organizations')"
          @keydown.enter="router.push('/organizations')"
          @keydown.space.prevent="router.push('/organizations')"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">{{ L.dashboard.organizations }}</span>
            <span class="text-indigo-600" v-html="ICONS.organizations"></span>
          </div>
          <div class="text-3xl font-bold text-slate-700">{{ stats.totalOrganizations }}</div>
          <div class="flex items-center gap-1 mt-1">
            <span v-html="trends.orgs >= 0 ? ICONS.trendUp : ICONS.trendDown" class="w-4 h-4" :class="trends.orgs >= 0 ? 'text-emerald-500' : 'text-red-500'"></span>
            <span class="text-xs font-medium" :class="trends.orgs >= 0 ? 'text-emerald-600' : 'text-red-600'">{{ Math.abs(trends.orgs) }}%</span>
            <span class="text-xs text-slate-400">{{ L.dashboard.monthly }}</span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6" data-testid="dashboard-charts">
        <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6" aria-labelledby="daily-trend-title">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 id="daily-trend-title" class="text-lg font-semibold text-slate-800">{{ L.dashboard.dailyTrend }}</h2>
              <p class="text-xs text-slate-500 mt-1">{{ L.dashboard.lastSevenDays }}</p>
            </div>
            <span class="text-xs text-slate-400">{{ trend.reduce((sum, item) => sum + item.count, 0) }} {{ L.dashboard.transactionsCount }}</span>
          </div>
          <div v-if="trend.length" class="overflow-x-auto" role="img" :aria-label="L.dashboard.chartLabel">
            <svg class="w-full min-w-[520px] h-64" viewBox="0 0 660 260" preserveAspectRatio="none">
              <line v-for="level in [0, 1, 2, 3, 4]" :key="level" x1="36" :y1="trendGridY(level)" x2="648" :y2="trendGridY(level)" stroke="#e2e8f0" stroke-width="1" />
              <text v-for="level in [0, 1, 2, 3, 4]" :key="`label-${level}`" x="30" :y="trendGridY(level) + 4" text-anchor="end" class="fill-slate-400 text-[10px]">{{ Math.round((trendMax * (4 - level)) / 4) }}</text>
              <g v-for="(item, index) in trend" :key="item.date">
                <rect :x="trendX(index)" :y="trendY(item.count)" width="48" :height="trendBarHeight(item.count)" rx="6" fill="#2563eb" opacity="0.88">
                  <title>{{ trendLabel(item.date) }}: {{ item.count }}</title>
                </rect>
                <text :x="trendX(index) + 24" y="246" text-anchor="middle" class="fill-slate-500 text-[10px]">{{ trendLabel(item.date) }}</text>
              </g>
            </svg>
          </div>
          <div v-else class="text-center py-16 text-slate-400 text-sm">{{ L.dashboard.noTrendData }}</div>
        </section>

        <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6" aria-labelledby="type-breakdown-title">
          <div class="flex items-center justify-between mb-4">
            <div>
              <h2 id="type-breakdown-title" class="text-lg font-semibold text-slate-800">{{ L.dashboard.transactionTypes }}</h2>
              <p class="text-xs text-slate-500 mt-1">{{ L.dashboard.mostUsedTypes }}</p>
            </div>
            <span class="text-xs text-slate-400">{{ byType.length }} {{ L.dashboard.types }}</span>
          </div>
          <div v-if="typeBars.length" class="space-y-4">
            <div v-for="item in typeBars" :key="item.key">
              <div class="flex items-center justify-between gap-3 text-sm mb-1">
                <span class="text-slate-700 truncate" :title="item.key">{{ item.key }}</span>
                <span class="text-slate-500 font-semibold tabular-nums">{{ item.count }}</span>
              </div>
              <div class="w-full h-3 bg-slate-100 rounded-full overflow-hidden" role="progressbar" :aria-valuenow="item.percent" aria-valuemin="0" aria-valuemax="100" :aria-label="`${item.key}: ${item.count}`">
                <div class="h-full rounded-full bg-indigo-500 transition-all duration-500" :style="{ width: `${item.percent}%` }"></div>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-16 text-slate-400 text-sm">{{ L.dashboard.noTypeData }}</div>
        </section>
      </div>

      <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-5 mb-6" aria-labelledby="smart-insights-title" data-testid="smart-insights">
        <div class="flex flex-wrap items-start justify-between gap-3 mb-4">
          <div>
            <h2 id="smart-insights-title" class="text-lg font-semibold text-slate-800">{{ L.dashboard.smartInsights }}</h2>
            <p class="text-xs text-slate-500 mt-1">{{ L.dashboard.smartSubtitle }}</p>
          </div>
          <span class="gov-badge bg-blue-50 text-blue-700">{{ smartInsights.length }} {{ L.dashboard.insightCount }}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <article v-for="insight in smartInsights" :key="insight.key" class="rounded-lg border p-4 min-w-0" :class="insight.cardClass">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <span class="text-[11px] font-semibold uppercase tracking-wide" :class="insight.textClass">{{ insight.priority }}</span>
                <h3 class="font-semibold text-sm text-slate-800 mt-1 break-words">{{ insight.title }}</h3>
              </div>
              <span class="shrink-0 text-lg" aria-hidden="true">{{ insight.icon }}</span>
            </div>
            <p class="text-xs text-slate-600 mt-2 leading-5">{{ insight.text }}</p>
            <router-link v-if="insight.to" :to="insight.to" class="inline-flex mt-3 text-xs font-medium text-blue-700 hover:text-blue-900">
              {{ insight.action }}
            </router-link>
          </article>
        </div>
      </section>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-slate-800">{{ L.dashboard.recentTransactions }}</h2>
            <router-link to="/transactionslist" class="text-sm text-blue-600 hover:text-blue-800 font-medium">
              {{ L.actions.viewAll }} ←
            </router-link>
          </div>
          <div v-if="recentTransactions.length === 0" class="text-center py-8 text-slate-400 text-sm">
            {{ L.tx.noTransactions }}
          </div>
          <div v-else class="space-y-2" role="status" aria-live="polite">
            <div
              v-for="tx in recentTransactions" :key="tx.id"
              v-memo="[tx.status, tx.transaction_no]"
              @click="router.push(`/transactiondetails?id=${tx.id}`)"
              @keydown.enter="router.push(`/transactiondetails?id=${tx.id}`)"
              @keydown.space.prevent="router.push(`/transactiondetails?id=${tx.id}`)"
              class="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors"
              tabindex="0" role="button"
              :aria-label="`${L.tx.transaction} ${tx.transaction_no} — ${statusLabel(tx.status)}`"
            >
              <div class="min-w-0 flex-1">
                <div class="font-medium text-slate-800 text-sm">{{ tx.transaction_no }}</div>
                <div class="text-xs text-slate-500 mt-0.5 truncate">
                  {{ tx.transaction_type }} — {{ tx.sender_name }}
                  <span v-if="tx.created_at" class="mr-1">· {{ formatDate(tx.created_at) }}</span>
                </div>
              </div>
              <span :class="statusClass(tx.status)" class="gov-badge mr-3">
                {{ statusLabel(tx.status) }}
              </span>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 class="text-lg font-semibold text-slate-800 mb-4">{{ L.dashboard.statusDistribution }}</h2>
            <div class="space-y-3">
              <div v-for="item in statusDistribution" :key="item.key">
                <div class="flex items-center justify-between text-sm mb-1">
                  <span class="text-slate-700">{{ item.label }}</span>
                  <span class="text-slate-500 font-medium">{{ item.count }}</span>
                </div>
                <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden" role="progressbar" :aria-valuenow="item.percent" aria-valuemin="0" aria-valuemax="100" :aria-label="`${item.label}: ${item.percent}%`">
                  <div
                    class="h-full rounded-full transition-all duration-500"
                    :class="item.barClass"
                    :style="{ width: item.percent + '%' }"
                  ></div>
                </div>
              </div>
              <div v-if="statusDistribution.length === 0" class="text-center py-4 text-slate-400 text-sm">{{ L.actions.noData }}</div>
            </div>
          </div>

          <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <h2 class="text-lg font-semibold text-slate-800 mb-4">{{ L.dashboard.quickActions }}</h2>
            <div class="space-y-3">
              <router-link to="/newtransaction"
                class="flex items-center gap-3 w-full p-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium"
                :aria-label="L.dashboard.newTransaction">
                <span v-html="ICONS.plus"></span>
                {{ L.dashboard.newTransaction }}
              </router-link>
              <router-link to="/transactionslist"
                class="flex items-center gap-3 w-full p-3 bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors text-sm font-medium"
                :aria-label="L.dashboard.searchTransactions">
                <span v-html="ICONS.search"></span>
                {{ L.dashboard.searchTransactions }}
              </router-link>
              <router-link to="/organizations"
                class="flex items-center gap-3 w-full p-3 bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors text-sm font-medium"
                :aria-label="L.dashboard.manageOrgs">
                <span v-html="ICONS.organizations"></span>
                {{ L.dashboard.manageOrgs }}
              </router-link>
              <router-link to="/reports"
                class="flex items-center gap-3 w-full p-3 bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors text-sm font-medium"
                :aria-label="L.dashboard.reports">
                <span v-html="ICONS.reports"></span>
                {{ L.dashboard.reports }}
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, shallowRef, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { dashboardApi } from '../api'
import { statusLabel, statusClass, formatDate } from '../composables/useStatus'
import { ICONS } from '../composables/useIcons'
import { L, useLocale } from '../composables/useLocale'

const router = useRouter()
const auth = useAuthStore()
const { locale } = useLocale()

const loading = ref(true)
const error = ref(null)
const stats = shallowRef({ totalTransactions: 0, approved: 0, draft: 0, rejected: 0, archived: 0, cancelled: 0, totalOrganizations: 0 })
const trends = ref({ total: 0, approved: 0, draft: 0, orgs: 0 })
const recentTransactions = ref([])
const statusDistribution = ref([])
const trend = ref([])
const byType = ref([])
const trendMax = computed(() => Math.max(...trend.value.map((item) => item.count), 1))
const typeBars = computed(() => {
  const max = Math.max(...byType.value.map((item) => item.count), 1)
  return byType.value.map((item) => ({ ...item, percent: Math.round((item.count / max) * 100) }))
})
const smartInsights = computed(() => {
  const items = []
  if (stats.value.draft > 0) {
    items.push({
      key: 'drafts',
      priority: stats.value.draft >= 5 ? L.dashboard.priorityHigh : L.dashboard.priorityMedium,
      title: `${L.dashboard.smartDraftTitle} (${stats.value.draft})`,
      text: L.dashboard.smartDraftText,
      action: L.dashboard.openDrafts,
      to: '/transactionslist?status=draft',
      icon: '!',
      cardClass: stats.value.draft >= 5 ? 'border-amber-300 bg-amber-50' : 'border-slate-200 bg-slate-50',
      textClass: 'text-amber-700',
    })
  }
  if (stats.value.rejected > 0) {
    items.push({
      key: 'rejected',
      priority: L.dashboard.priorityHigh,
      title: `${L.dashboard.smartRejectedTitle} (${stats.value.rejected})`,
      text: L.dashboard.smartRejectedText,
      action: L.dashboard.openRejected,
      to: '/transactionslist?status=rejected',
      icon: '!',
      cardClass: 'border-red-300 bg-red-50',
      textClass: 'text-red-700',
    })
  }
  if (trends.value.total < 0) {
    items.push({
      key: 'trend',
      priority: L.dashboard.priorityMedium,
      title: L.dashboard.smartTrendTitle,
      text: L.dashboard.smartTrendText,
      action: L.dashboard.searchTransactions,
      to: '/transactionslist',
      icon: '↘',
      cardClass: 'border-blue-200 bg-blue-50',
      textClass: 'text-blue-700',
    })
  }
  if (!items.length) {
    items.push({
      key: 'healthy',
      priority: L.dashboard.priorityLow,
      title: L.dashboard.smartHealthyTitle,
      text: L.dashboard.smartHealthyText,
      action: L.dashboard.viewAll,
      to: '/reports',
      icon: '✓',
      cardClass: 'border-emerald-200 bg-emerald-50',
      textClass: 'text-emerald-700',
    })
  }
  return items.slice(0, 3)
})

function trendX(index) {
  return 44 + index * 86
}

function trendY(count) {
  return 220 - trendBarHeight(count)
}

function trendBarHeight(count) {
  return Math.max(4, Math.round((Number(count || 0) / trendMax.value) * 190))
}

function trendGridY(level) {
  return 30 + level * 47.5
}

function trendLabel(value) {
  const date = new Date(`${value}T00:00:00`)
  return new Intl.DateTimeFormat(locale.value === 'ar' ? 'ar-IQ' : 'en-US', { day: 'numeric', month: 'short' }).format(date)
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const response = await dashboardApi.summary({ days: 7, lang: locale.value })
    const payload = response.data || {}
    const summary = payload.summary || {}
    const byStatus = summary.by_status || {}
    const total = Object.values(byStatus).reduce((sum, count) => sum + Number(count || 0), 0)

    stats.value = {
      totalTransactions: Number(summary.total_transactions || 0),
      approved: Number(byStatus.approved || 0),
      draft: Number(byStatus.draft || 0),
      rejected: Number(byStatus.rejected || 0),
      archived: Number(byStatus.archived || 0),
      cancelled: Number(byStatus.cancelled || 0),
      totalOrganizations: Number(summary.total_organizations || 0),
    }
    recentTransactions.value = payload.recent_transactions || []
    trend.value = payload.trend || []
    byType.value = payload.by_type || []
    trends.value = {
      total: Number(payload.trends?.total || 0),
      approved: Number(payload.trends?.approved || 0),
      draft: Number(payload.trends?.draft || 0),
      orgs: Number(payload.trends?.orgs || 0),
    }

    statusDistribution.value = Object.entries(byStatus)
      .filter(([, count]) => Number(count) > 0)
      .map(([key, count]) => ({
        key,
        count: Number(count),
        label: statusLabel(key),
        percent: total ? Math.round((Number(count) / total) * 100) : 0,
        barClass: {
          approved: 'bg-emerald-500',
          draft: 'bg-amber-500',
          rejected: 'bg-red-500',
          archived: 'bg-slate-500',
          cancelled: 'bg-slate-400',
        }[key] || 'bg-blue-500',
      }))
  } catch (e) {
    error.value = e.apiMessage || e.response?.data?.message || e.response?.data?.detail || L.errors.loadFailed
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
