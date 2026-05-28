<template>
  <div>
    <div class="flex items-center gap-3 mb-6">
      <router-link to="/transactionslist" class="text-blue-600 hover:text-blue-800">&larr; العودة</router-link>
      <h1 class="text-2xl font-bold text-slate-800">تفاصيل المعاملة</h1>
    </div>
    <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
    <div v-else-if="error" class="bg-red-50 text-red-600 text-sm p-4 rounded-lg">{{ error }}</div>
    <div v-else-if="!tx" class="text-center py-12 text-slate-400">المعاملة غير موجودة</div>
    <div v-else class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">{{ tx.transaction_no }}</h2>
          <span :class="statusClass(tx.status)" class="px-3 py-1 rounded-full text-sm font-medium">
            {{ statusLabel(tx.status) }}
          </span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div><span class="text-slate-500">النوع:</span> {{ tx.transaction_type }}</div>
          <div><span class="text-slate-500">التاريخ:</span> {{ tx.transaction_date }}</div>
          <div><span class="text-slate-500">المرسل:</span> {{ tx.sender_name }}</div>
          <div><span class="text-slate-500">المستلم:</span> {{ tx.receiver_name }}</div>
          <div><span class="text-slate-500">رقم التفويض:</span> {{ tx.authorization_no || '-' }}</div>
          <div><span class="text-slate-500">تاريخ التفويض:</span> {{ tx.authorization_date || '-' }}</div>
          <div v-if="tx.notes" class="md:col-span-2"><span class="text-slate-500">ملاحظات:</span> {{ tx.notes }}</div>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 class="text-lg font-semibold mb-4">البنود</h3>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="border-b border-slate-200">
                <th class="text-right py-2 px-3">نوع العينة</th>
                <th class="text-center py-2 px-3">المجموع</th>
                <th class="text-center py-2 px-3">صالح</th>
                <th class="text-center py-2 px-3">تالف</th>
                <th class="text-center py-2 px-3">مرفوض</th>
                <th class="text-center py-2 px-3">غير مطابق</th>
                <th class="text-center py-2 px-3">حالة النقل</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in tx.items" :key="item.id" class="border-b border-slate-100">
                <td class="py-2 px-3 font-medium">{{ item.sample_type }}</td>
                <td class="text-center py-2 px-3">{{ item.total_count }}</td>
                <td class="text-center py-2 px-3 text-emerald-600">{{ item.valid_count }}</td>
                <td class="text-center py-2 px-3 text-red-600">{{ item.damaged_count }}</td>
                <td class="text-center py-2 px-3 text-red-600">{{ item.rejected_count }}</td>
                <td class="text-center py-2 px-3 text-amber-600">{{ item.nonconforming_count }}</td>
                <td class="text-center py-2 px-3">{{ item.transport_condition }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="auth.isAdmin || auth.userRole === 'supervisor'" class="flex gap-3">
        <button @click="updateStatus('approved')" class="bg-emerald-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-emerald-700">اعتماد</button>
        <button @click="updateStatus('rejected')" class="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700">رفض</button>
        <button @click="updateStatus('archived')" class="bg-slate-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-slate-700">أرشفة</button>
        <button @click="deleteTxn" class="bg-red-800 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-900">حذف</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { transactionsApi } from '../api'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const tx = ref(null)
const loading = ref(true)
const error = ref(null)

function statusLabel(status) {
  const labels = { draft: 'مسودة', approved: 'معتمد', rejected: 'مرفوض', archived: 'مؤرشف', cancelled: 'ملغي' }
  return labels[status] || status
}

function statusClass(status) {
  const classes = {
    draft: 'bg-amber-50 text-amber-700',
    approved: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-700',
    archived: 'bg-slate-100 text-slate-600',
    cancelled: 'bg-slate-100 text-slate-600',
  }
  return classes[status] || 'bg-slate-100 text-slate-600'
}

async function updateStatus(newStatus) {
  try {
    const res = await transactionsApi.update(route.query.id, { status: newStatus })
    tx.value = res.data
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل في تحديث الحالة'
  }
}

async function deleteTxn() {
  if (!confirm('هل أنت متأكد من حذف هذه المعاملة؟')) return
  try {
    await transactionsApi.delete(route.query.id)
    router.push('/transactionslist')
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل في حذف المعاملة'
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
