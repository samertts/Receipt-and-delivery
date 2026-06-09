<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">المؤسسات</h1>
      <button @click="showForm = true" v-if="auth.isAdmin || auth.userRole === 'supervisor'" class="gov-btn-primary">
        <span v-html="icons.plus"></span>
        إضافة مؤسسة
      </button>
    </div>

    <div v-if="loading" class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="p-4 space-y-3">
        <div v-for="i in 4" :key="i" class="skeleton h-12 w-full"></div>
      </div>
    </div>

    <div v-else-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3">
      <span v-html="icons.alert"></span>
      <span>{{ error }}</span>
      <button @click="fetchData" class="mr-auto text-red-600 hover:text-red-800 font-medium">إعادة المحاولة</button>
    </div>

    <div v-else>
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50 border-b border-slate-200">
              <th class="text-right py-3 px-4 font-medium text-slate-600">الاسم</th>
              <th class="text-right py-3 px-4 font-medium text-slate-600">الرمز</th>
              <th class="text-right py-3 px-4 font-medium text-slate-600">الهاتف</th>
              <th class="text-right py-3 px-4 font-medium text-slate-600">البريد</th>
              <th class="text-right py-3 px-4 font-medium text-slate-600">المحافظة</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="org in items" :key="org.id" class="border-b border-slate-100 hover:bg-blue-50 transition-colors">
              <td class="py-3 px-4 font-medium text-slate-800">{{ org.name }}</td>
              <td class="py-3 px-4">
                <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs font-mono">{{ org.code }}</span>
              </td>
              <td class="py-3 px-4 text-slate-600">{{ org.phone || '-' }}</td>
              <td class="py-3 px-4 text-slate-600">{{ org.email || '-' }}</td>
              <td class="py-3 px-4 text-slate-600">{{ org.address || '-' }}</td>
            </tr>
            <tr v-if="items.length === 0">
              <td colspan="5" class="text-center py-12 text-slate-400">لا توجد مؤسسات</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Teleport to="body">
      <Transition name="dialog">
        <div v-if="showForm" class="fixed inset-0 z-[9998] flex items-center justify-center p-4">
          <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" @click="showForm = false"></div>
          <div class="relative bg-white rounded-2xl shadow-2xl p-6 w-full max-w-lg border border-slate-200" dir="rtl">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold text-slate-800">إضافة مؤسسة جديدة</h2>
              <button @click="showForm = false" class="text-slate-400 hover:text-slate-600" aria-label="إغلاق">
                <span v-html="icons.close"></span>
              </button>
            </div>
            <div v-if="formError" class="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg mb-4 flex items-center gap-2">
              <span v-html="icons.alert"></span>
              <span>{{ formError }}</span>
            </div>
            <div class="space-y-3">
              <input v-model="newOrg.name" placeholder="اسم المؤسسة" required class="gov-input" />
              <input v-model="newOrg.code" placeholder="الرمز" required class="gov-input" />
              <input v-model="newOrg.address" placeholder="المحافظة" class="gov-input" />
              <input v-model="newOrg.phone" placeholder="الهاتف" class="gov-input" type="tel" />
              <input v-model="newOrg.email" placeholder="البريد الإلكتروني" class="gov-input" type="email" />
            </div>
            <div class="flex gap-3 mt-6">
              <button @click="createOrg" :disabled="submitting" class="gov-btn-primary flex-1">
                <span v-if="submitting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>{{ submitting ? 'جاري الحفظ...' : 'حفظ' }}</span>
              </button>
              <button @click="showForm = false" class="gov-btn-secondary flex-1">إلغاء</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useUiStore } from '../stores/ui'
import { organizationsApi } from '../api'
import { ICONS } from '../composables/useIcons'

const auth = useAuthStore()
const ui = useUiStore()
const icons = ICONS

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
    ui.success('تم إنشاء المؤسسة بنجاح')
    await fetchData()
  } catch (e) {
    formError.value = e.response?.data?.detail || 'فشل في إنشاء المؤسسة'
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.dialog-enter-active { transition: all 0.2s ease-out; }
.dialog-leave-active { transition: all 0.15s ease-in; }
.dialog-enter-from, .dialog-leave-to { opacity: 0; }
.dialog-enter-from > div:last-child { transform: scale(0.95); }
</style>
