<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <h1 class="text-2xl font-bold text-slate-800">سجل التدقيق</h1>
      <select v-model="actionFilter" @change="fetchData" class="gov-select sm:w-56">
        <option value="">جميع الإجراءات</option>
        <option value="login_success">تسجيل دخول</option>
        <option value="login_failed">فشل تسجيل دخول</option>
        <option value="login_blocked">حظر تسجيل دخول</option>
        <option value="logout">تسجيل خروج</option>
        <option value="token_refreshed">تحديث رمز</option>
        <option value="password_changed">تغيير كلمة مرور</option>
        <option value="transaction_created">إنشاء معاملة</option>
        <option value="transaction_updated">تحديث معاملة</option>
        <option value="transaction_deleted">حذف معاملة</option>
        <option value="user_created">إنشاء مستخدم</option>
        <option value="user_updated">تحديث مستخدم</option>
        <option value="user_deleted">حذف مستخدم</option>
        <option value="org_created">إنشاء مؤسسة</option>
        <option value="org_updated">تحديث مؤسسة</option>
        <option value="org_deleted">حذف مؤسسة</option>
      </select>
    </div>

    <div v-if="!auth.isAuthenticated || (auth.userRole !== 'admin' && auth.userRole !== 'auditor')"
      class="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-lg flex items-center gap-2">
      <span v-html="icons.alert"></span>
      <span>ليس لديك صلاحية الوصول إلى سجل التدقيق</span>
    </div>

    <div v-else>
      <div v-if="loading" class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="p-4 space-y-3">
          <div v-for="i in 5" :key="i" class="skeleton h-10 w-full"></div>
        </div>
      </div>
      <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
        <span v-html="icons.alert"></span>
        <span>{{ error }}</span>
        <button @click="fetchData" class="mr-auto text-red-600 hover:text-red-800 font-medium">إعادة المحاولة</button>
      </div>
      <div v-else-if="logs.length === 0" class="text-center py-16 bg-white rounded-xl shadow-sm border border-slate-200">
        <div class="text-slate-300 text-5xl mb-4" v-html="icons.doc"></div>
        <p class="text-slate-500 text-sm">لا توجد سجلات</p>
      </div>
      <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 border-b border-slate-200">
                <th class="text-right py-3 px-4 font-medium text-slate-600">التاريخ</th>
                <th class="text-right py-3 px-4 font-medium text-slate-600">المستخدم</th>
                <th class="text-right py-3 px-4 font-medium text-slate-600">الإجراء</th>
                <th class="text-right py-3 px-4 font-medium text-slate-600">IP</th>
                <th class="text-right py-3 px-4 font-medium text-slate-600">التفاصيل</th>
                <th class="text-center py-3 px-4 font-medium text-slate-600">التغييرات</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id" class="border-b border-slate-100 hover:bg-blue-50 transition-colors">
                <td class="py-3 px-4 text-xs text-slate-500 whitespace-nowrap">{{ formatDate(log.created_at) }}</td>
                <td class="py-3 px-4">
                  <span class="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{{ log.user_id?.substring(0, 8) || '-' }}</span>
                </td>
                <td class="py-3 px-4">
                  <span :class="actionBadgeClass(log.action_type)" class="gov-badge">
                    {{ actionLabel(log.action_type) }}
                  </span>
                </td>
                <td class="py-3 px-4 text-xs text-slate-500 font-mono">{{ log.ip_address }}</td>
                <td class="py-3 px-4 text-xs text-slate-500 max-w-xs truncate">{{ log.details }}</td>
                <td class="py-3 px-4 text-xs text-center">
                  <span v-if="log.changes_json" @click="viewChangesJson(log)" class="cursor-pointer text-blue-600 underline hover:text-blue-800">JSON</span>
                  <span v-else class="text-slate-300">-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useUiStore } from '../stores/ui'
import { auditLogsApi } from '../api'
import { ICONS } from '../composables/useIcons'

const auth = useAuthStore()
const ui = useUiStore()
const icons = ICONS

const logs = ref([])
const loading = ref(true)
const error = ref(null)
const actionFilter = ref('')

const DOC_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-16 h-16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`
icons.doc = DOC_ICON

const actionLabels = {
  login_success: 'تسجيل دخول',
  login_failed: 'فشل تسجيل دخول',
  login_blocked: 'حظر تسجيل دخول',
  logout: 'تسجيل خروج',
  token_refreshed: 'تحديث رمز',
  password_changed: 'تغيير كلمة مرور',
  transaction_created: 'إنشاء معاملة',
  transaction_updated: 'تحديث معاملة',
  transaction_deleted: 'حذف معاملة',
  user_created: 'إنشاء مستخدم',
  user_updated: 'تحديث مستخدم',
  user_deleted: 'حذف مستخدم',
  org_created: 'إنشاء مؤسسة',
  org_updated: 'تحديث مؤسسة',
  org_deleted: 'حذف مؤسسة',
}

function actionLabel(action) {
  return actionLabels[action] || action
}

function actionBadgeClass(action) {
  if (action?.includes('success') || action?.includes('created')) return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
  if (action?.includes('failed') || action?.includes('blocked') || action?.includes('deleted')) return 'bg-red-50 text-red-700 ring-1 ring-red-200'
  if (action?.includes('updated') || action?.includes('changed')) return 'bg-amber-50 text-amber-700 ring-1 ring-amber-200'
  return 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ar-IQ')
}

function viewChangesJson(log) {
  try {
    const parsed = JSON.parse(log.changes_json)
    ui.info(JSON.stringify(parsed, null, 2))
  } catch {
    ui.info(log.changes_json)
  }
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const params = {}
    if (actionFilter.value) params.action_type = actionFilter.value
    const res = await auditLogsApi.list(params)
    logs.value = res.data
  } catch (e) {
    error.value = 'فشل في تحميل سجل التدقيق'
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
