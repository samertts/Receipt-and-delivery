<template>
  <div class="min-h-screen bg-slate-50" dir="rtl">
    <div v-if="auth.isAuthenticated" class="flex h-screen overflow-hidden">
      <Sidebar
        :collapsed="ui.sidebarCollapsed"
        @toggle="ui.toggleSidebar"
      />
      <main class="flex-1 overflow-y-auto bg-slate-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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

const auth = useAuthStore()
const ui = useUiStore()
</script>
