<template>
  <div class="fixed top-4 left-4 z-50" :dir="locale === 'ar' ? 'rtl' : 'ltr'">
    <button
      type="button"
      class="relative w-11 h-11 rounded-full bg-white border border-slate-200 shadow-md text-slate-600 hover:text-primary-900 hover:border-blue-300 transition-colors flex items-center justify-center"
      :aria-label="L.notifications.open"
      :aria-expanded="open"
      @click="open = !open"
    >
      <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9a6 6 0 1 0-12 0v.75a8.967 8.967 0 0 1-2.31 6.022c1.733.64 3.555 1.083 5.454 1.31m5.713 0a24.255 24.255 0 0 1-5.713 0m5.713 0a3 3 0 1 1-5.713 0" />
      </svg>
      <span
        v-if="notifications.unreadCount"
        class="absolute -top-1 -right-1 min-w-5 h-5 px-1 rounded-full bg-red-600 text-white text-[10px] font-bold flex items-center justify-center"
        :aria-label="L.notifications.unreadCount"
      >{{ notifications.unreadCount > 99 ? '99+' : notifications.unreadCount }}</span>
    </button>

    <section
      v-if="open"
      class="absolute left-0 mt-3 w-[min(22rem,calc(100vw-2rem))] bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden"
      :aria-label="L.notifications.title"
    >
      <header class="flex items-center justify-between gap-3 p-4 border-b border-slate-100">
        <div>
          <h2 class="font-semibold text-slate-800">{{ L.notifications.title }}</h2>
          <p class="text-[11px] mt-1" :class="notifications.connected ? 'text-emerald-600' : 'text-slate-400'">
            {{ notifications.connected ? L.notifications.connected : notifications.connecting ? L.notifications.connecting : L.notifications.disconnected }}
          </p>
        </div>
        <button v-if="notifications.unreadCount" type="button" class="text-xs text-blue-600 hover:text-blue-800" @click="notifications.markAllRead">
          {{ L.notifications.markAllRead }}
        </button>
      </header>

      <div v-if="notifications.lastError" class="px-4 py-2 text-xs text-red-600 bg-red-50">
        {{ notifications.lastError }}
      </div>

      <div v-if="!notifications.notifications.length" class="p-8 text-center text-sm text-slate-400">
        {{ L.notifications.empty }}
      </div>
      <div v-else class="max-h-96 overflow-y-auto divide-y divide-slate-100">
        <button
          v-for="item in notifications.notifications"
          :key="item.id"
          type="button"
          class="w-full text-right p-4 hover:bg-slate-50 transition-colors"
          :class="{ 'bg-blue-50/60': !item.read }"
          @click="openNotification(item)"
        >
          <div class="flex items-start gap-3">
            <span class="mt-1 w-2 h-2 rounded-full shrink-0" :class="item.read ? 'bg-slate-300' : 'bg-blue-600'"></span>
            <span class="min-w-0 flex-1">
              <strong class="block text-sm text-slate-800">{{ item.title }}</strong>
              <span class="block mt-1 text-xs text-slate-500">{{ item.message }}</span>
              <time class="block mt-2 text-[10px] text-slate-400">{{ formatNotificationDate(item.created_at) }}</time>
            </span>
          </div>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '../stores/notifications'
import { L, useLocale } from '../composables/useLocale'

const router = useRouter()
const notifications = useNotificationStore()
const { locale } = useLocale()
const open = ref(false)

function formatNotificationDate(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat(locale.value === 'ar' ? 'ar-IQ' : 'en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(date)
}

function openNotification(item) {
  notifications.markRead(item.id)
  if (item.transaction_id) router.push(`/transactiondetails?id=${item.transaction_id}`)
}

onMounted(notifications.connect)
onBeforeUnmount(notifications.disconnect)
</script>
