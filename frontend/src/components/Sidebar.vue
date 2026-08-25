<template>
  <aside
    class="bg-slate-900 text-white flex flex-col transition-all duration-300 shrink-0"
    :class="collapsed ? 'w-16' : 'w-64'"
    :dir="locale === 'ar' ? 'rtl' : 'ltr'"
  >
    <div class="h-16 flex items-center px-4 border-b border-slate-800">
      <div v-if="!collapsed" class="flex flex-col">
        <span class="text-base font-bold text-white">{{ appName }}</span>
        <span class="text-[10px] text-slate-400 leading-tight">{{ L.appSubtitle }}</span>
      </div>

      <div v-else class="mx-auto text-lg font-bold text-white">{{ locale === 'ar' ? 'م' : 'L' }}</div>
    </div>

    <nav class="flex-1 overflow-y-auto py-4 px-2 space-y-1 scrollbar-thin">
      <template v-for="group in navGroups" :key="group.title">
        <div v-if="!collapsed" class="text-[10px] text-slate-500 px-3 pb-1 pt-3 font-bold tracking-wide">
          {{ group.title }}
        </div>
        <router-link
          v-for="item in group.items"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150"
          :class="isActive(item.path)
            ? 'bg-blue-600/20 text-blue-300 border-r-2 border-blue-400'
            : 'text-slate-300 hover:bg-slate-800/50 hover:text-white'"
          :title="collapsed ? item.label : ''"
        >
          <span class="shrink-0 w-5 h-5 flex items-center justify-center" v-html="item.icon"></span>
          <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
        </router-link>
      </template>
    </nav>

    <div class="border-t border-slate-800 p-3">
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-sm font-bold shrink-0 shadow-lg"
        >
          {{ initials }}
        </div>
        <div v-if="!collapsed" class="flex-1 min-w-0">
          <div class="text-sm font-medium truncate text-white">{{ auth.user?.username }}</div>
          <div class="text-[11px] text-slate-400">{{ roleLabel }}</div>
        </div>
      </div>
      <button
        @click="toggleLocale"
        class="mt-2 w-full flex items-center justify-center gap-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800 py-1.5 rounded-lg transition-colors"
        :title="locale === 'ar' ? L.switchToEnglish : L.switchToArabic"
        :aria-label="locale === 'ar' ? L.switchToEnglish : L.switchToArabic"
      >
        <span class="font-bold">{{ locale === 'ar' ? 'EN' : 'ع' }}</span>
        <span v-if="!collapsed">{{ locale === 'ar' ? L.switchToEnglish : L.switchToArabic }}</span>
      </button>
      <button
        @click="logout"
        class="mt-2 w-full flex items-center justify-center gap-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-900/20 py-1.5 rounded-lg transition-colors"
        :class="{ 'text-center': collapsed }"
        :title="collapsed ? L.actions.logout : ''"
      >
        <span v-html="icons.logout"></span>
        <span v-if="!collapsed">{{ L.actions.logout }}</span>
      </button>
    </div>

    <button
      @click="$emit('toggle')"
      class="h-9 text-slate-400 hover:text-white hover:bg-slate-800 text-sm transition-colors shrink-0 flex items-center justify-center"
      :title="collapsed ? L.actions.expand : L.actions.collapse"
      :aria-label="collapsed ? L.actions.expand : L.actions.collapse"
    >
      <span v-html="collapsed ? icons.collapseLeft : icons.collapseRight"></span>
    </button>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { L, useLocale } from '../composables/useLocale'
import { ICONS } from '../composables/useIcons'
import { roleLabel } from '../composables/useStatus'

defineProps({
  collapsed: Boolean,
})

defineEmits(['toggle'])

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const icons = ICONS

const { locale, toggleLocale } = useLocale()
const appName = computed(() => L.appName)

const navGroups = computed(() => [
  {
    title: L.nav.operations,
    items: [
      { path: '/dashboard', label: L.nav.dashboard, icon: ICONS.dashboard, permission: 'view_dashboard' },
      { path: '/transactionslist', label: L.nav.transactions, icon: ICONS.transactions, permission: 'view_transactions' },
      { path: '/newtransaction', label: L.nav.newTransaction, icon: ICONS.newTransaction, permission: 'create_transaction' },
    ],
  },
  {
    title: L.nav.admin,
    items: [
      { path: '/organizations', label: L.nav.organizations, icon: ICONS.organizations, permission: 'view_organizations' },
      { path: '/auditlogs', label: L.nav.auditLogs, icon: ICONS.auditLogs, permission: 'view_audit_logs' },
    ],
  },
  {
    title: L.nav.reports,
    items: [
      { path: '/reports', label: L.nav.reportsTitle, icon: ICONS.reports, permission: 'view_reports' },
    ],
  },
  {
    title: L.nav.system,
    items: [
      { path: '/settings', label: L.nav.settings, icon: ICONS.settings, permission: 'manage_settings' },
      { path: '/devices', label: L.nav.devices, icon: ICONS.settings, permission: 'use_devices' },
    ],
  },
].map((group) => ({
  ...group,
  items: group.items.filter((item) => !item.permission || auth.hasPermission(item.permission)),
})).filter((group) => group.items.length))

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
