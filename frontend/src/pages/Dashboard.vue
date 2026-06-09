<template>
  <div>
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-slate-800">مرحباً، {{ auth.user?.username || 'مستخدم' }}</h1>
      <p class="text-sm text-slate-500 mt-1">لوحة التحكم — نظرة عامة على نظام الاستلام والتسليم المختبري</p>
    </div>

    <div v-if="loading">
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

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
      <span v-html="icons.alert" class="shrink-0"></span>
      <span>{{ error }}</span>
      <button @click="loadData" class="mr-auto text-red-600 hover:text-red-800 font-medium">إعادة المحاولة</button>
    </div>

    <div v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">إجمالي المعاملات</span>
            <span class="text-blue-600" v-html="icons.transactions"></span>
          </div>
          <div class="text-3xl font-bold text-primary-900">{{ stats.totalTransactions }}</div>
          <div class="text-xs text-slate-400 mt-1">جميع المعاملات في النظام</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">معتمدة</span>
            <span class="text-emerald-600" v-html="icons.check"></span>
          </div>
          <div class="text-3xl font-bold text-emerald-600">{{ stats.approved }}</div>
          <div class="text-xs text-slate-400 mt-1">المعاملات المعتمدة</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">مسودة</span>
            <span class="text-amber-600" v-html="icons.edit"></span>
          </div>
          <div class="text-3xl font-bold text-amber-600">{{ stats.draft }}</div>
          <div class="text-xs text-slate-400 mt-1">بانتظار الاعتماد</div>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md transition-shadow">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-slate-500">المؤسسات</span>
            <span class="text-indigo-600" v-html="icons.organizations"></span>
          </div>
          <div class="text-3xl font-bold text-slate-700">{{ stats.totalOrganizations }}</div>
          <div class="text-xs text-slate-400 mt-1">الجهات المسجلة</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-slate-800">آخر المعاملات</h2>
            <router-link to="/transactionslist" class="text-sm text-blue-600 hover:text-blue-800 font-medium">
              عرض الكل ←
            </router-link>
          </div>
          <div v-if="recentTransactions.length === 0" class="text-center py-8 text-slate-400 text-sm">
            لا توجد معاملات بعد
          </div>
          <div v-else class="space-y-2">
            <div
              v-for="tx in recentTransactions" :key="tx.id"
              @click="router.push(`/transactiondetails?id=${tx.id}`)"
              class="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors"
            >
              <div class="min-w-0 flex-1">
                <div class="font-medium text-slate-800 text-sm">{{ tx.transaction_no }}</div>
                <div class="text-xs text-slate-500 mt-0.5 truncate">{{ tx.transaction_type }} — {{ tx.sender_name }}</div>
              </div>
              <span :class="statusClass(tx.status)" class="gov-badge mr-3">
                {{ statusLabel(tx.status) }}
              </span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 class="text-lg font-semibold text-slate-800 mb-4">إجراءات سريعة</h2>
          <div class="space-y-3">
            <router-link to="/newtransaction"
              class="flex items-center gap-3 w-full p-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors text-sm font-medium">
              <span v-html="icons.plus"></span>
              معاملة جديدة
            </router-link>
            <router-link to="/transactionslist"
              class="flex items-center gap-3 w-full p-3 bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors text-sm font-medium">
              <span v-html="icons.search"></span>
              بحث في المعاملات
            </router-link>
            <router-link to="/organizations"
              class="flex items-center gap-3 w-full p-3 bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors text-sm font-medium">
              <span v-html="icons.organizations"></span>
              إدارة المؤسسات
            </router-link>
            <router-link to="/reports"
              class="flex items-center gap-3 w-full p-3 bg-slate-50 text-slate-700 rounded-lg hover:bg-slate-100 transition-colors text-sm font-medium">
              <span v-html="icons.reports"></span>
              التقارير
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { transactionsApi, organizationsApi } from '../api'
import { statusLabel, statusClass } from '../composables/useStatus'
import { ICONS } from '../composables/useIcons'

const router = useRouter()
const auth = useAuthStore()
const icons = ICONS

const loading = ref(true)
const error = ref(null)
const stats = ref({ totalTransactions: 0, approved: 0, draft: 0, totalOrganizations: 0 })
const recentTransactions = ref([])

const EDIT_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`

icons.edit = EDIT_ICON

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [txRes, orgRes, approvedRes, draftRes] = await Promise.all([
      transactionsApi.list({ limit: 5 }),
      organizationsApi.list({ limit: 1 }),
      transactionsApi.list({ limit: 1, status: 'approved' }),
      transactionsApi.list({ limit: 1, status: 'draft' }),
    ])
    recentTransactions.value = txRes.data
    stats.value.totalTransactions = parseInt(txRes.headers['x-total-count'] || 0)
    stats.value.approved = parseInt(approvedRes.headers['x-total-count'] || 0)
    stats.value.draft = parseInt(draftRes.headers['x-total-count'] || 0)
    stats.value.totalOrganizations = parseInt(orgRes.headers['x-total-count'] || 0)
  } catch (e) {
    error.value = 'فشل في تحميل البيانات'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
