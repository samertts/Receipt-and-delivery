<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">الإعدادات</h1>
    <div v-if="!auth.isAdmin" class="bg-amber-50 text-amber-700 p-4 rounded-lg">ليس لديك صلاحية الوصول إلى هذه الصفحة</div>
    <div v-else class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      <div>
        <h2 class="text-lg font-semibold mb-4">إدارة المستخدمين</h2>
        <div v-if="usersLoading" class="text-sm text-slate-400">جاري التحميل...</div>
        <div v-else>
          <div class="overflow-x-auto mb-4">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-slate-200">
                  <th class="text-right py-2 px-3">اسم المستخدم</th>
                  <th class="text-right py-2 px-3">الاسم الكامل</th>
                  <th class="text-right py-2 px-3">الصلاحية</th>
                  <th class="text-right py-2 px-3">الحالة</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id" class="border-b border-slate-100">
                  <td class="py-2 px-3">{{ u.username }}</td>
                  <td class="py-2 px-3">{{ u.full_name }}</td>
                  <td class="py-2 px-3">{{ u.role }}</td>
                  <td class="py-2 px-3">{{ u.status }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <details class="border border-slate-200 rounded-lg p-4">
            <summary class="cursor-pointer text-sm font-medium text-blue-700">إضافة مستخدم جديد</summary>
            <div class="mt-3 space-y-3">
              <div v-if="userError" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">{{ userError }}</div>
              <div v-if="userSuccess" class="bg-emerald-50 text-emerald-600 text-sm p-3 rounded-lg">{{ userSuccess }}</div>
              <input v-model="newUser.username" placeholder="اسم المستخدم"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
              <input v-model="newUser.full_name" placeholder="الاسم الكامل"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
              <input v-model="newUser.password" type="password" placeholder="كلمة المرور"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg" />
              <select v-model="newUser.role"
                class="w-full px-4 py-2 border border-slate-300 rounded-lg">
                <option value="user">مستخدم</option>
                <option value="supervisor">مشرف</option>
                <option value="auditor">مدقق</option>
                <option value="admin">مدير</option>
              </select>
              <button @click="createUser" :disabled="userSubmitting"
                class="bg-blue-900 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-800 disabled:opacity-50">
                {{ userSubmitting ? 'جاري...' : 'حفظ' }}
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

const auth = useAuthStore()
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
