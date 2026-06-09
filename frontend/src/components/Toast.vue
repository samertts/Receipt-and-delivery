<template>
  <Teleport to="body">
    <div
      class="fixed bottom-4 left-1/2 -translate-x-1/2 z-[9999] flex flex-col gap-2 pointer-events-none"
      dir="rtl"
    >
      <TransitionGroup name="toast">
        <div
          v-for="t in ui.toasts"
          :key="t.id"
          class="pointer-events-auto flex items-center gap-3 px-5 py-3 rounded-xl shadow-lg border text-sm font-medium min-w-[320px] max-w-[480px] animate-slide-up"
          :class="toastClass(t.type)"
        >
          <span v-html="toastIcon(t.type)" class="shrink-0"></span>
          <span class="flex-1">{{ t.message }}</span>
          <button @click="ui.removeToast(t.id)" class="opacity-60 hover:opacity-100 transition-opacity" aria-label="إغلاق">
            <span v-html="icons.close"></span>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup>
import { useUiStore } from '../stores/ui'
import { ICONS } from '../composables/useIcons'

const ui = useUiStore()
const icons = ICONS

function toastClass(type) {
  return {
    success: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    error: 'bg-red-50 text-red-800 border-red-200',
    warning: 'bg-amber-50 text-amber-800 border-amber-200',
    info: 'bg-blue-50 text-blue-800 border-blue-200',
  }[type] || 'bg-white text-slate-800 border-slate-200'
}

function toastIcon(type) {
  return {
    success: ICONS.check,
    error: ICONS.close,
    warning: ICONS.alert,
    info: ICONS.info,
  }[type] || ICONS.info
}
</script>

<style scoped>
.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from { opacity: 0; transform: translateY(20px) scale(0.95); }
.toast-leave-to { opacity: 0; transform: translateY(-10px) scale(0.95); }
.animate-slide-up { animation: slideUp 0.3s ease-out; }
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
