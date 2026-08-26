<template>
  <div class="app-shell min-h-screen" :dir="direction">
    <div v-if="auth.isAuthenticated" class="flex h-screen min-h-0 overflow-hidden">
      <NotificationCenter />
      <Sidebar
        :collapsed="ui.sidebarCollapsed"
        @toggle="ui.toggleSidebar"
      />
      <main class="app-main flex-1 min-w-0 min-h-0 app-scroll-container">
        <div class="w-full min-w-0 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <router-view />
        </div>
      </main>
    </div>
    <router-view v-else />
    <Toast />
  </div>
</template>

<script setup>
import { useAuthStore } from '../stores/auth'
import { useUiStore } from '../stores/ui'
import Sidebar from './Sidebar.vue'
import Toast from './Toast.vue'
import NotificationCenter from './NotificationCenter.vue'
import { useLocale } from '../composables/useLocale'

const auth = useAuthStore()
const ui = useUiStore()
const { direction } = useLocale()
</script>
