<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <router-link to="/transactionslist" class="text-blue-600 hover:text-blue-800 flex items-center gap-1 text-sm font-medium">
        <span v-html="icons.arrowRight"></span>
        العودة
      </router-link>
      <h1 class="text-2xl font-bold text-slate-800">تفاصيل المعاملة</h1>
    </div>

    <div v-if="loading" class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="skeleton h-6 w-48 mb-4"></div>
        <div class="grid grid-cols-2 gap-4">
          <div v-for="i in 6" :key="i" class="skeleton h-5 w-full"></div>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="skeleton h-5 w-24 mb-4"></div>
        <div v-for="i in 3" :key="i" class="skeleton h-8 w-full mb-2"></div>
      </div>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
      <span v-html="icons.alert"></span>
      <span>{{ error }}</span>
    </div>

    <div v-else-if="!tx" class="text-center py-12 text-slate-400 bg-white rounded-xl border border-slate-200">
      المعاملة غير موجودة
    </div>

    <div v-else class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold text-slate-800">{{ tx.transaction_no }}</h2>
          <span :class="statusClass(tx.status)" class="gov-badge text-sm px-3 py-1">
            {{ statusLabel(tx.status) }}
          </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div class="flex items-center gap-2">
            <span class="text-slate-400" v-html="icons.tag"></span>
            <span class="text-slate-500">النوع:</span>
            <span class="font-medium text-slate-700">{{ tx.transaction_type }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400" v-html="icons.calendar"></span>
            <span class="text-slate-500">التاريخ:</span>
            <span class="font-medium text-slate-700">{{ tx.transaction_date }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400" v-html="icons.user"></span>
            <span class="text-slate-500">المرسل:</span>
            <span class="font-medium text-slate-700">{{ tx.sender_name }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-slate-400" v-html="icons.user"></span>
            <span class="text-slate-500">المستلم:</span>
            <span class="font-medium text-slate-700">{{ tx.receiver_name }}</span>
          </div>
          <div v-if="tx.sender_job_title" class="flex items-center gap-2">
            <span class="text-slate-500">مسمى المرسل:</span>
            <span class="font-medium text-slate-700">{{ tx.sender_job_title }}</span>
          </div>
          <div v-if="tx.receiver_job_title" class="flex items-center gap-2">
            <span class="text-slate-500">مسمى المستلم:</span>
            <span class="font-medium text-slate-700">{{ tx.receiver_job_title }}</span>
          </div>
          <div v-if="tx.transport_info"><span class="text-slate-500">معلومات النقل:</span> {{ tx.transport_info }}</div>
          <div><span class="text-slate-500">رقم التفويض:</span> {{ tx.authorization_no || '-' }}</div>
          <div><span class="text-slate-500">تاريخ التفويض:</span> {{ tx.authorization_date || '-' }}</div>
          <div v-if="tx.notes" class="md:col-span-2">
            <span class="text-slate-500">ملاحظات:</span>
            <p class="mt-1 text-slate-700 bg-slate-50 p-3 rounded-lg">{{ tx.notes }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-slate-800">البنود</h3>
          <span class="text-xs text-slate-400">{{ tx.items?.length || 0 }} بند</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200 bg-slate-50">
                <th class="text-right py-3 px-4 font-medium text-slate-600">نوع العينة</th>
                <th class="text-center py-3 px-4 font-medium text-slate-600">المجموع</th>
                <th class="text-center py-3 px-4 font-medium text-emerald-600">صالح</th>
                <th class="text-center py-3 px-4 font-medium text-red-600">تالف</th>
                <th class="text-center py-3 px-4 font-medium text-red-600">مرفوض</th>
                <th class="text-center py-3 px-4 font-medium text-amber-600">غير مطابق</th>
                <th class="text-center py-3 px-4 font-medium text-slate-600">حالة النقل</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in tx.items" :key="item.id" class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                <td class="py-3 px-4 font-medium text-slate-800">{{ item.sample_type }}</td>
                <td class="text-center py-3 px-4 font-semibold">{{ item.total_count }}</td>
                <td class="text-center py-3 px-4 text-emerald-600 font-medium">{{ item.valid_count }}</td>
                <td class="text-center py-3 px-4 text-red-600">{{ item.damaged_count }}</td>
                <td class="text-center py-3 px-4 text-red-600">{{ item.rejected_count }}</td>
                <td class="text-center py-3 px-4 text-amber-600">{{ item.nonconforming_count }}</td>
                <td class="text-center py-3 px-4">{{ item.transport_condition }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="flex flex-wrap gap-3">
        <div v-if="auth.isAdmin || auth.userRole === 'supervisor'" class="flex flex-wrap gap-3">
          <button @click="updateStatus('approved')" class="gov-btn-success flex items-center gap-2">
            <span v-html="icons.check"></span>
            اعتماد
          </button>
          <button @click="updateStatus('rejected')" class="gov-btn-danger flex items-center gap-2">
            <span v-html="icons.close"></span>
            رفض
          </button>
          <button @click="updateStatus('archived')" class="gov-btn-secondary flex items-center gap-2">
            <span v-html="icons.archive"></span>
            أرشفة
          </button>
        </div>
        <button
          v-if="auth.isAdmin"
          @click="showDeleteConfirm = true"
          class="gov-btn flex items-center gap-2 bg-red-800 text-white hover:bg-red-900"
        >
          <span v-html="icons.delete"></span>
          حذف
        </button>
      </div>
    </div>

    <ConfirmDialog
      :visible="showDeleteConfirm"
      title="حذف المعاملة"
      message="هل أنت متأكد من حذف هذه المعاملة؟ لا يمكن التراجع عن هذا الإجراء."
      confirmText="حذف"
      cancelText="إلغاء"
      variant="danger"
      @confirm="deleteTxn"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useUiStore } from '../stores/ui'
import { transactionsApi } from '../api'
import { statusLabel, statusClass } from '../composables/useStatus'
import { ICONS } from '../composables/useIcons'
import ConfirmDialog from '../components/ConfirmDialog.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const ui = useUiStore()
const icons = ICONS

const tx = ref(null)
const loading = ref(true)
const error = ref(null)
const showDeleteConfirm = ref(false)

const TAG_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>`
const USER_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
const ARCHIVE_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="21 8 21 21 3 21 3 8"/><rect x="1" y="3" width="22" height="5"/><line x1="10" y1="12" x2="14" y2="12"/></svg>`
const DELETE_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`
icons.tag = TAG_ICON
icons.user = USER_ICON
icons.archive = ARCHIVE_ICON
icons.delete = DELETE_ICON

async function updateStatus(newStatus) {
  try {
    const res = await transactionsApi.update(route.query.id, { status: newStatus })
    tx.value = res.data
    ui.success(`تم ${statusLabel(newStatus)} المعاملة بنجاح`)
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل في تحديث الحالة'
    ui.error(error.value)
  }
}

async function deleteTxn() {
  showDeleteConfirm.value = false
  try {
    await transactionsApi.delete(route.query.id)
    ui.success('تم حذف المعاملة بنجاح')
    router.push('/transactionslist')
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل في حذف المعاملة'
    ui.error(error.value)
  }
}

onMounted(async () => {
  if (!route.query.id) {
    error.value = 'لم يتم تحديد معاملة'
    loading.value = false
    return
  }
  try {
    const res = await transactionsApi.get(route.query.id)
    tx.value = res.data
  } catch (e) {
    error.value = 'فشل في تحميل المعاملة'
  } finally {
    loading.value = false
  }
})
</script>
