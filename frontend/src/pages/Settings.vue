<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">الإعدادات</h1>

    <div v-if="!auth.isAdmin" class="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-lg flex items-center gap-2">
      <span v-html="icons.alert"></span>
      <span>ليس لديك صلاحية الوصول إلى هذه الصفحة</span>
    </div>

    <div v-else class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <span class="text-slate-600" v-html="icons.users"></span>
          إدارة المستخدمين
        </h2>
        <div v-if="usersLoading" class="space-y-2">
          <div v-for="i in 3" :key="i" class="skeleton h-10 w-full"></div>
        </div>
        <div v-else>
          <div class="overflow-x-auto mb-4">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-200 bg-slate-50">
                  <th class="text-right py-3 px-4 font-medium text-slate-600">اسم المستخدم</th>
                  <th class="text-right py-3 px-4 font-medium text-slate-600">الاسم الكامل</th>
                  <th class="text-right py-3 px-4 font-medium text-slate-600">الصلاحية</th>
                  <th class="text-right py-3 px-4 font-medium text-slate-600">الحالة</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id" class="border-b border-slate-100 hover:bg-slate-50 transition-colors">
                  <td class="py-3 px-4 font-medium text-slate-800">{{ u.username }}</td>
                  <td class="py-3 px-4 text-slate-600">{{ u.full_name }}</td>
                  <td class="py-3 px-4">
                    <span class="gov-badge bg-blue-50 text-blue-700 ring-1 ring-blue-200">{{ u.role }}</span>
                  </td>
                  <td class="py-3 px-4">
                    <span class="gov-badge" :class="u.status === 'active' ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' : 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'">
                      {{ u.status === 'active' ? 'نشط' : 'غير نشط' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <details class="border border-slate-200 rounded-xl overflow-hidden">
            <summary class="cursor-pointer text-sm font-medium text-blue-700 px-4 py-3 hover:bg-blue-50 transition-colors">
              إضافة مستخدم جديد
            </summary>
            <div class="p-4 space-y-3 border-t border-slate-200">
              <div v-if="userError" class="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg flex items-center gap-2">
                <span v-html="icons.alert"></span>
                <span>{{ userError }}</span>
              </div>
              <div v-if="userSuccess" class="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm p-3 rounded-lg flex items-center gap-2">
                <span v-html="icons.check"></span>
                <span>{{ userSuccess }}</span>
              </div>
              <input v-model="newUser.username" placeholder="اسم المستخدم" class="gov-input" />
              <input v-model="newUser.full_name" placeholder="الاسم الكامل" class="gov-input" />
              <input v-model="newUser.password" type="password" placeholder="كلمة المرور" class="gov-input" />
              <select v-model="newUser.role" class="gov-select">
                <option value="user">مستخدم</option>
                <option value="supervisor">مشرف</option>
                <option value="auditor">مدقق</option>
                <option value="admin">مدير</option>
              </select>
              <button @click="createUser" :disabled="userSubmitting" class="gov-btn-primary">
                <span v-if="userSubmitting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span>{{ userSubmitting ? 'جاري...' : 'حفظ' }}</span>
              </button>
            </div>
          </details>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { usersApi } from '../api'
import { ICONS } from '../composables/useIcons'

const auth = useAuthStore()
const icons = ICONS

const users = ref([])
const usersLoading = ref(true)
const userError = ref(null)
const userSuccess = ref(null)
const userSubmitting = ref(false)
const newUser = ref({ username: '', full_name: '', password: '', role: 'user' })

async function fetchUsers() {
  usersLoading.value = true
  try {
    const res = await usersApi.list()
    users.value = res.data
  } catch (e) {
    // ignore
  } finally {
    usersLoading.value = false
  }
}

async function createUser() {
  userSubmitting.value = true
  userError.value = null
  userSuccess.value = null
  try {
    await usersApi.create(newUser.value)
    userSuccess.value = 'تم إنشاء المستخدم بنجاح'
    newUser.value = { username: '', full_name: '', password: '', role: 'user' }
    await fetchUsers()
  } catch (e) {
    userError.value = e.response?.data?.detail || 'فشل في إنشاء المستخدم'
  } finally {
    userSubmitting.value = false
  }
}

onMounted(fetchUsers)
</script>
