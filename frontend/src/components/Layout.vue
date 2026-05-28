<template>
  <div class="min-h-screen bg-slate-50" dir="rtl">
    <nav class="bg-white shadow-sm border-b border-slate-200" v-if="auth.isAuthenticated">
      <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between h-16">
          <div class="flex items-center space-x-4 space-x-reverse">
            <router-link to="/dashboard" class="text-lg font-bold text-blue-900">
              {{ appName }}
            </router-link>
            <router-link
              v-for="item in navItems"
              :key="item.path"
              :to="item.path"
              class="px-3 py-2 text-sm rounded-md transition-colors"
              :class="isActive(item.path) ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:text-slate-900'"
            >
              {{ item.label }}
            </router-link>
          </div>
          <div class="flex items-center space-x-4 space-x-reverse">
            <span class="text-sm text-slate-500">{{ auth.user?.username }} ({{ roleLabel }})</span>
            <button @click="logout" class="text-sm text-red-600 hover:text-red-800">تسجيل خروج</button>
          </div>
        </div>
      </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 py-6">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const appName = 'نظام إدارة الاستلام المختبري'

const navItems = [
  { path: '/dashboard', label: 'لوحة التحكم' },
  { path: '/transactionslist', label: 'المعاملات' },
  { path: '/newtransaction', label: 'معاملة جديدة' },
  { path: '/organizations', label: 'المؤسسات' },
  { path: '/reports', label: 'التقارير' },
  { path: '/settings', label: 'الإعدادات' },
  { path: '/auditlogs', label: 'سجل التدقيق' },
]

const roleLabels = {
  admin: 'مدير',
  supervisor: 'مشرف',
  user: 'مستخدم',
  auditor: 'مدقق',
}

const roleLabel = computed(() => roleLabels[auth.userRole] || auth.userRole)

function isActive(path) {
  return route.path === path
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>
