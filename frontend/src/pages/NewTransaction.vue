<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">معاملة جديدة</h1>
    <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
    <form v-else @submit.prevent="submitForm" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      <div v-if="error" class="bg-red-50 text-red-600 text-sm p-4 rounded-lg">{{ error }}</div>
      <div v-if="success" class="bg-emerald-50 text-emerald-600 text-sm p-4 rounded-lg">تم إنشاء المعاملة بنجاح: {{ success }}</div>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">نوع المعاملة</label>
          <input v-model="form.transaction_type" required placeholder例: Sample Receipt"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">تاريخ المعاملة</label>
          <input v-model="form.transaction_date" type="date" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">المرسل</label>
          <input v-model="form.sender_name" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">المستلم</label>
          <input v-model="form.receiver_name" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">معرف المؤسسة المرسلة</label>
          <input v-model="form.sender_organization_id" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">معرف المؤسسة المستلمة</label>
          <input v-model="form.receiver_organization_id" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">رقم التفويض</label>
          <input v-model="form.authorization_no"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">تاريخ التفويض</label>
          <input v-model="form.authorization_date" type="date"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500" />
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">ملاحظات</label>
        <textarea v-model="form.notes" rows="3"
          class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500"></textarea>
      </div>
      <div>
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-slate-800">بنود المعاملة</h2>
          <button type="button" @click="addItem" class="text-sm text-blue-600 hover:text-blue-800">+ إضافة بند</button>
        </div>
        <div v-for="(item, idx) in form.items" :key="idx"
          class="bg-slate-50 rounded-lg p-4 mb-3 border border-slate-200">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div>
              <label class="block text-xs text-slate-500">نوع العينة</label>
              <input v-model="item.sample_type" required
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500">المجموع</label>
              <input v-model.number="item.total_count" type="number" min="1" required
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500">صالح</label>
              <input v-model.number="item.valid_count" type="number" min="0" required
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500">تالف</label>
              <input v-model.number="item.damaged_count" type="number" min="0" required
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500">مرفوض</label>
              <input v-model.number="item.rejected_count" type="number" min="0" required
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500">غير مطابق</label>
              <input v-model.number="item.nonconforming_count" type="number" min="0" required
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500">حالة النقل</label>
              <input v-model="item.transport_condition"
                class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div class="flex items-end">
              <button type="button" @click="removeItem(idx)" class="text-red-500 text-sm hover:text-red-700">حذف</button>
            </div>
          </div>
        </div>
      </div>
      <button type="submit" :disabled="submitting"
        class="w-full bg-blue-900 text-white py-2.5 rounded-lg font-medium hover:bg-blue-800 transition-colors disabled:opacity-50">
        {{ submitting ? 'جاري الحفظ...' : 'حفظ المعاملة' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { transactionsApi } from '../api'

const loading = ref(false)
const submitting = ref(false)
const error = ref(null)
const success = ref(null)

const form = ref({
  transaction_type: '',
  transaction_date: new Date().toISOString().split('T')[0],
  sender_name: '',
  receiver_name: '',
  sender_organization_id: '',
  receiver_organization_id: '',
  authorization_no: '',
  authorization_date: '',
  notes: '',
  status: 'draft',
  items: [
    { sample_type: '', total_count: 1, valid_count: 1, damaged_count: 0, rejected_count: 0, nonconforming_count: 0, transport_condition: '', notes: '' },
  ],
})

function addItem() {
  form.value.items.push({ sample_type: '', total_count: 1, valid_count: 0, damaged_count: 0, rejected_count: 0, nonconforming_count: 0, transport_condition: '', notes: '' })
}

function removeItem(idx) {
  if (form.value.items.length > 1) {
    form.value.items.splice(idx, 1)
  }
}

async function submitForm() {
  submitting.value = true
  error.value = null
  success.value = null
  try {
    const result = await transactionsApi.create(form.value)
    success.value = result.data.transaction_no
    form.value = {
      transaction_type: '',
      transaction_date: new Date().toISOString().split('T')[0],
      sender_name: '',
      receiver_name: '',
      sender_organization_id: '',
      receiver_organization_id: '',
      authorization_no: '',
      authorization_date: '',
      notes: '',
      status: 'draft',
      items: [{ sample_type: '', total_count: 1, valid_count: 1, damaged_count: 0, rejected_count: 0, nonconforming_count: 0, transport_condition: '', notes: '' }],
    }
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل في إنشاء المعاملة'
  } finally {
    submitting.value = false
  }
}

onMounted(() => { loading.value = false })
</script>
