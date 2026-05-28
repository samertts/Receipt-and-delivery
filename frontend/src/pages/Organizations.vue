<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">المؤسسات</h1>
      <button @click="showForm = true" v-if="auth.isAdmin || auth.userRole === 'supervisor'"
        class="bg-blue-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-800">إضافة مؤسسة</button>
    </div>
    <div v-if="loading" class="text-center py-12 text-slate-400">جاري التحميل...</div>
    <div v-else-if="error" class="bg-red-50 text-red-600 text-sm p-4 rounded-lg">{{ error }}</div>
    <div v-else>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200">
              <th class="text-right py-3 px-4">الاسم</th>
              <th class="text-right py-3 px-4">الرمز</th>
              <th class="text-right py-3 px-4">الهاتف</th>
              <th class="text-right py-3 px-4">البريد</th>
              <th class="text-right py-3 px-4">المحافظة</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="org in items" :key="org.id" class="border-b border-slate-100 hover:bg-slate-50">
              <td class="py-3 px-4 font-medium">{{ org.name }}</td>
              <td class="py-3 px-4">{{ org.code }}</td>
              <td class="py-3 px-4">{{ org.phone || '-' }}</td>
              <td class="py-3 px-4">{{ org.email || '-' }}</td>
              <td class="py-3 px-4">{{ org.address || '-' }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="5" class="text-center py-8 text-slate-400">لا توجد مؤسسات</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-if="showForm" class="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-xl p-6 w-full max-w-lg">
        <h2 class="text-lg font-semibold mb-4">إضافة مؤسسة جديدة</h2>
        <div v-if="formError" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg mb-4">{{ formError }}</div>
        <div class="space-y-3">
          <input v-model="newOrg.name" placeholder="اسم المؤسسة" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
          <input v-model="newOrg.code" placeholder="الرمز" required
            class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
          <input v-model="newOrg.address" placeholder="المحافظة"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
          <input v-model="newOrg.phone" placeholder="الهاتف"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
          <input v-model="newOrg.email" placeholder="البريد الإلكتروني"
            class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
        </div>
        <div class="flex gap-3 mt-4">
          <button @click="createOrg" :disabled="submitting"
            class="flex-1 bg-blue-900 text-white py-2 rounded-lg hover:bg-blue-800 disabled:opacity-50">
            {{ submitting ? 'جاري الحفظ...' : 'حفظ' }}
          </button>
          <button @click="showForm = false"
            class="flex-1 bg-slate-200 text-slate-700 py-2 rounded-lg hover:bg-slate-300">إلغاء</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { organizationsApi } from '../api'

const auth = useAuthStore()
const items = ref([])
const loading = ref(true)
const error = ref(null)
const showForm = ref(false)
const submitting = ref(false)
const formError = ref(null)
const newOrg = ref({ name: '', code: '', address: '', phone: '', email: '' })

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await organizationsApi.list()
    items.value = res.data
  } catch (e) {
    error.value = 'فشل في تحميل المؤسسات'
  } finally {
    loading.value = false
  }
}

async function createOrg() {
  submitting.value = true
  formError.value = null
  try {
    await organizationsApi.create(newOrg.value)
    showForm.value = false
    newOrg.value = { name: '', code: '', address: '', phone: '', email: '' }
    await fetchData()
  } catch (e) {
    formError.value = e.response?.data?.detail || 'فشل في إنشاء المؤسسة'
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>
