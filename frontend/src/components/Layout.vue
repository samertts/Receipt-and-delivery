<template>
  <div class="min-h-screen bg-slate-50" dir="rtl">
    <div v-if="auth.isAuthenticated" class="flex h-screen overflow-hidden">
      <aside
        class="bg-slate-800 text-white flex flex-col transition-all duration-300 shrink-0"
        :class="collapsed ? 'w-16' : 'w-60'"
      >
        <div class="h-16 flex items-center px-4 border-b border-slate-700">
          <div v-if="!collapsed" class="flex flex-col">
            <span class="text-base font-bold text-white">{{ appName }}</span>
            <span class="text-[10px] text-slate-400 leading-tight">نظام الاستلام والتسليم المختبري</span>
          </div>
          <div v-else class="mx-auto text-lg font-bold text-white">م</div>
        </div>

        <nav class="flex-1 overflow-y-auto py-4 px-2 space-y-1">
          <template v-for="group in navGroups" :key="group.title">
            <div v-if="!collapsed" class="text-[11px] text-slate-500 px-3 pb-1 pt-3 font-medium">
              {{ group.title }}
            </div>
            <router-link
              v-for="item in group.items"
              :key="item.path"
              :to="item.path"
              class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors"
              :class="isActive(item.path)
                ? 'bg-blue-600/20 text-blue-300 border-r-2 border-blue-400'
                : 'text-slate-300 hover:bg-slate-700/50 hover:text-white'"
              :title="item.label"
            >
              <span class="text-lg shrink-0 w-5 text-center" v-html="item.icon"></span>
              <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
            </router-link>
          </template>
        </nav>

        <div class="border-t border-slate-700 p-3">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold shrink-0">
              {{ initials }}
            </div>
            <div v-if="!collapsed" class="flex-1 min-w-0">
              <div class="text-sm font-medium truncate text-white">{{ auth.user?.username }}</div>
              <div class="text-[11px] text-slate-400">{{ roleLabel }}</div>
            </div>
          </div>
          <button
            @click="logout"
            class="mt-2 w-full text-xs text-red-400 hover:text-red-300 py-1.5 rounded transition-colors"
            :class="{ 'text-center': collapsed }"
          >
            {{ collapsed ? '✕' : 'تسجيل خروج' }}
          </button>
        </div>

        <button
          @click="collapsed = !collapsed"
          class="h-8 text-slate-400 hover:text-white hover:bg-slate-700 text-sm transition-colors shrink-0"
        >
          {{ collapsed ? '→' : '←' }}
        </button>
      </aside>

      <main class="flex-1 overflow-y-auto">
        <div class="max-w-7xl mx-auto px-6 py-6">
          <router-view />
        </div>
      </main>
    </div>
    <router-view v-else />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const collapsed = ref(false)
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const appName = 'الاستلام المختبري'

const navGroups = [
  {
    title: 'العمليات',
    items: [
      { path: '/dashboard', label: 'لوحة التحكم', icon: '&#9751;' },
      { path: '/transactionslist', label: 'المعاملات', icon: '&#9776;' },
      { path: '/newtransaction', label: 'معاملة جديدة', icon: '&#43;' },
    ],
  },
  {
    title: 'الإدارة',
    items: [
      { path: '/organizations', label: 'المؤسسات', icon: '&#9733;' },
      { path: '/auditlogs', label: 'سجل التدقيق', icon: '&#9776;' },
    ],
  },
  {
    title: 'التقارير',
    items: [
      { path: '/reports', label: 'التقارير', icon: '&#128196;' },
    ],
  },
  {
    title: 'النظام',
    items: [
      { path: '/settings', label: 'الإعدادات', icon: '&#9881;' },
    ],
  },
]

const roleLabels = {
  admin: 'مدير',
  supervisor: 'مشرف',
  user: 'مستخدم',
  auditor: 'مدقق',
}

const roleLabel = computed(() => roleLabels[auth.userRole] || auth.userRole)

const initials = computed(() => {
  const name = auth.user?.username || ''
  return name.slice(0, 2).toUpperCase()
})

function isActive(path) {
  return route.path === path
}

function logout() {
  auth.logout()
  router.push('/')
}
</script>
