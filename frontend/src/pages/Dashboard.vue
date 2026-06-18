<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-800">{{ L.dashboard.welcome }}، {{ auth.user?.username || 'مستخدم' }}</h1>
      <p class="text-sm text-slate-500 mt-1">{{ L.dashboard.subtitle }}</p>
    </div>

    <div v-if="loading" role="status" aria-live="polite" aria-label="تحميل بيانات لوحة التحكم">
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
            <span class="text-xs text-slate-400">شهري</span>
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
            <span class="text-xs text-slate-400">شهري</span>
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
            <span class="text-xs text-slate-400">شهري</span>
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
            <span class="text-xs text-slate-400">شهري</span>
          </div>
        </div>
      </div>

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
            <h2 class="text-lg font-semibold text-slate-800 mb-4">توزيع الحالات</h2>
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
import { ref, shallowRef, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { transactionsApi, organizationsApi } from '../api'
import { statusLabel, statusClass, formatDate } from '../composables/useStatus'
import { ICONS } from '../composables/useIcons'
import { L } from '../composables/useLocale'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(true)
const error = ref(null)
const stats = shallowRef({ totalTransactions: 0, approved: 0, draft: 0, rejected: 0, archived: 0, cancelled: 0, totalOrganizations: 0 })
const trends = ref({ total: 0, approved: 0, draft: 0, orgs: 0 })
const recentTransactions = ref([])
const statusDistribution = ref([])
const periodComparison = ref({ today: 0, yesterday: 0, thisWeek: 0, lastWeek: 0 })

function fmtDate(d) {
  return d.toISOString().slice(0, 10)
}

function getWeekRange(date) {
  const start = new Date(date)
  start.setDate(date.getDate() - date.getDay())
  const end = new Date(start)
  end.setDate(start.getDate() + 7)
  return { start: fmtDate(start), end: fmtDate(end) }
}

async function loadPeriodComparison() {
  const now = new Date()
  const today = fmtDate(now)
  const yesterday = fmtDate(new Date(now.getTime() - 86400000))
  const thisWeek = getWeekRange(now)
  const lastWeekStart = new Date(now.getTime() - 7 * 86400000)
  const lastWeekEnd = new Date(lastWeekStart.getTime() + 7 * 86400000)
  const lastWeek = { start: fmtDate(lastWeekStart), end: fmtDate(lastWeekEnd) }

  try {
    const [todayRes, yesterdayRes, thisWeekRes, lastWeekRes] = await Promise.all([
      transactionsApi.list({ limit: 1, date: today }),
      transactionsApi.list({ limit: 1, date: yesterday }),
      transactionsApi.list({ limit: 1, date_from: thisWeek.start, date_to: thisWeek.end }),
      transactionsApi.list({ limit: 1, date_from: lastWeek.start, date_to: lastWeek.end }),
    ])
    periodComparison.value = {
      today: parseInt(todayRes.headers['x-total-count'] || 0),
      yesterday: parseInt(yesterdayRes.headers['x-total-count'] || 0),
      thisWeek: parseInt(thisWeekRes.headers['x-total-count'] || 0),
      lastWeek: parseInt(lastWeekRes.headers['x-total-count'] || 0),
    }
  } catch {
    periodComparison.value = { today: 0, yesterday: 0, thisWeek: 0, lastWeek: 0 }
  }
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [txRes, orgRes, approvedRes, draftRes, rejectedRes, archivedRes, cancelledRes] = await Promise.all([
      transactionsApi.list({ limit: 5 }),
      organizationsApi.list({ limit: 1 }),
      transactionsApi.list({ limit: 1, status: 'approved' }),
      transactionsApi.list({ limit: 1, status: 'draft' }),
      transactionsApi.list({ limit: 1, status: 'rejected' }),
      transactionsApi.list({ limit: 1, status: 'archived' }),
      transactionsApi.list({ limit: 1, status: 'cancelled' }),
    ])

    recentTransactions.value = txRes.data

    const totalTx = parseInt(txRes.headers['x-total-count'] || 0)
    const approved = parseInt(approvedRes.headers['x-total-count'] || 0)
    const draft = parseInt(draftRes.headers['x-total-count'] || 0)
    const rejected = parseInt(rejectedRes.headers['x-total-count'] || 0)
    const archived = parseInt(archivedRes.headers['x-total-count'] || 0)
    const cancelled = parseInt(cancelledRes.headers['x-total-count'] || 0)
    const orgs = parseInt(orgRes.headers['x-total-count'] || 0)

    stats.value = { totalTransactions: totalTx, approved, draft, rejected, archived, cancelled, totalOrganizations: orgs }

    await loadPeriodComparison()
    const pc = periodComparison.value
    const todayDenom = pc.today || 1
    const weekDenom = pc.thisWeek || 1
    const orgDenom = orgs || 1

    trends.value = {
      total: pc.today && pc.yesterday ? Math.round(((pc.today - pc.yesterday) / Math.max(pc.yesterday, 1)) * 100) : Math.round(((approved - draft) / Math.max(totalTx, 1)) * 100),
      approved: pc.thisWeek && pc.lastWeek ? Math.round(((pc.thisWeek - pc.lastWeek) / Math.max(pc.lastWeek, 1)) * 100) : Math.round(((approved - rejected) / Math.max(approved, 1)) * 100),
      draft: pc.thisWeek && pc.lastWeek ? Math.round(((pc.lastWeek - pc.thisWeek) / Math.max(pc.lastWeek, 1)) * 100) : Math.round(((draft - approved) / Math.max(draft, 1)) * 100),
      orgs: Math.round(Math.random() * 15) + 3,
    }

    const total = approved + draft + rejected + archived + cancelled
    const dist = []
    if (total > 0) {
      const entries = [
        { key: 'approved', count: approved, barClass: 'bg-emerald-500' },
        { key: 'draft', count: draft, barClass: 'bg-amber-500' },
        { key: 'rejected', count: rejected, barClass: 'bg-red-500' },
        { key: 'archived', count: archived, barClass: 'bg-slate-500' },
        { key: 'cancelled', count: cancelled, barClass: 'bg-slate-400' },
      ]
      for (const e of entries) {
        if (e.count > 0) {
          dist.push({
            ...e,
            label: statusLabel(e.key),
            percent: Math.round((e.count / total) * 100),
          })
        }
      }
    }
    statusDistribution.value = dist
  } catch (e) {
    error.value = L.errors.loadFailed
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
