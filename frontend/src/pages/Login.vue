<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-slate-100 p-4">
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-lg p-8 border border-slate-200">
        <div class="text-center mb-8">
          <h1 class="text-2xl font-bold text-blue-900">نظام إدارة الاستلام المختبري</h1>
          <p class="text-slate-500 mt-2 text-sm">تسجيل الدخول إلى النظام</p>
        </div>
        <form @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">اسم المستخدم</label>
            <input
              v-model="username"
              type="text"
              required
              class="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              placeholder="أدخل اسم المستخدم"
              :disabled="loading"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">كلمة المرور</label>
            <input
              v-model="password"
              type="password"
              required
              class="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
              placeholder="أدخل كلمة المرور"
              :disabled="loading"
            />
          </div>
          <div v-if="error" class="bg-red-50 text-red-600 text-sm p-3 rounded-lg">
            {{ error }}
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-blue-900 text-white py-2.5 rounded-lg font-medium hover:bg-blue-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading">جاري تسجيل الدخول...</span>
            <span v-else>دخول</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref(null)
const loading = ref(false)

async function handleLogin() {
  error.value = null
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل تسجيل الدخول'
  } finally {
    loading.value = false
  }
}
</script>
