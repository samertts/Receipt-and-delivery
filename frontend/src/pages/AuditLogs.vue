<template>
  <div>
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
      <h1 class="text-2xl font-bold text-slate-800">{{ L.audit.title }}</h1>
      <select v-model="actionFilter" @change="fetchData" class="gov-select sm:w-56">
        <option value="">{{ L.audit.allActions }}</option>
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
      <span v-html="ICONS.alert"></span>
      <span>{{ L.audit.noPermission }}</span>
    </div>

    <div v-else>
      <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3 mb-4">
        <span v-html="ICONS.alert"></span>
        <span>{{ error }}</span>
        <button @click="fetchData" class="mr-auto text-red-600 hover:text-red-800 font-medium">{{ L.actions.retry }}</button>
      </div>

      <DataTable
        :columns="columns"
        :rows="logs"
        :loading="loading"
        row-key="id"
      >
        <template #empty>
          <div class="flex flex-col items-center gap-2">
            <span class="text-slate-300 text-4xl" v-html="ICONS.doc"></span>
            <p class="text-sm">{{ L.audit.noLogs }}</p>
          </div>
        </template>

        <template #cell-created_at="{ row }">
          <span class="text-xs text-slate-500 whitespace-nowrap">{{ formatDate(row.created_at) }}</span>
        </template>

        <template #cell-user_id="{ row }">
          <span class="font-mono text-xs bg-slate-100 px-1.5 py-0.5 rounded">{{ row.user_id?.substring(0, 8) || '-' }}</span>
        </template>

        <template #cell-action_type="{ row }">
          <span :class="actionBadgeClass(row.action_type)" class="gov-badge">
            {{ actionLabel(row.action_type) }}
          </span>
        </template>

        <template #cell-ip_address="{ row }">
          <span class="text-xs text-slate-500 font-mono">{{ row.ip_address }}</span>
        </template>

        <template #cell-details="{ row }">
          <div class="flex items-center gap-2">
            <span class="text-xs text-slate-500 max-w-xs truncate">{{ row.details }}</span>
            <span v-if="row.changes_json" @click.stop="viewChangesJson(row)" class="cursor-pointer text-blue-600 underline hover:text-blue-800 text-xs shrink-0">JSON</span>
          </div>
        </template>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useUiStore } from '../stores/ui'
import { auditLogsApi } from '../api'
import { ICONS } from '../composables/useIcons'
import { L } from '../composables/useLocale'
import DataTable from '../components/DataTable.vue'

const auth = useAuthStore()
const ui = useUiStore()

const logs = ref([])
const loading = ref(true)
const error = ref(null)
const actionFilter = ref('')

const columns = [
  { key: 'created_at', label: L.audit.date, sortable: true },
  { key: 'user_id', label: L.audit.user, sortable: true },
  { key: 'action_type', label: L.audit.action, sortable: true },
  { key: 'ip_address', label: L.audit.ip, sortable: true },
  { key: 'details', label: L.audit.details, sortable: false },
]

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
    error.value = L.errors.loadFailedAudit
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
</script>
