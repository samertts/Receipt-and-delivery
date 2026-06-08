<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">سجل التدقيق</h1>
      <select v-model="actionFilter" @change="fetchData"
        class="px-4 py-2 border border-slate-300 rounded-lg text-sm">
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
      class="bg-amber-50 text-amber-700 p-4 rounded-lg">
      ليس لديك صلاحية الوصول إلى سجل التدقيق
    </div>
    <div v-else>
      <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
      <div v-else-if="error" class="bg-red-50 text-red-600 text-sm p-4 rounded-lg">{{ error }}</div>
      <div v-else-if="logs.length === 0" class="text-center py-12 text-slate-400">لا توجد سجلات</div>
      <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200">
              <th class="text-right py-3 px-4">التاريخ</th>
              <th class="text-right py-3 px-4">المستخدم</th>
              <th class="text-right py-3 px-4">الإجراء</th>
              <th class="text-right py-3 px-4">IP</th>
              <th class="text-right py-3 px-4">التفاصيل</th>
              <th class="text-center py-3 px-4">التغييرات</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in logs" :key="log.id" class="border-b border-slate-100 hover:bg-slate-50">
              <td class="py-3 px-4 text-xs">{{ formatDate(log.created_at) }}</td>
              <td class="py-3 px-4 font-mono text-xs">{{ log.user_id?.substring(0, 8) || '-' }}</td>
              <td class="py-3 px-4">{{ actionLabel(log.action_type) }}</td>
              <td class="py-3 px-4">{{ log.ip_address }}</td>
              <td class="py-3 px-4 text-xs text-slate-500 max-w-xs truncate">{{ log.details }}</td>
              <td class="py-3 px-4 text-xs text-center">
                <span v-if="log.changes_json" @click="viewChangesJson(log)" class="cursor-pointer text-blue-600 underline">JSON</span>
                <span v-else class="text-slate-300">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { auditLogsApi } from '../api'

const auth = useAuthStore()
const logs = ref([])
const loading = ref(true)
const error = ref(null)
const actionFilter = ref('')

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

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ar-IQ')
}

function viewChangesJson(log) {
  try {
    const parsed = JSON.parse(log.changes_json)
    alert(JSON.stringify(parsed, null, 2))
  } catch {
    alert(log.changes_json)
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
