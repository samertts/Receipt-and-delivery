<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div v-if="visible" class="fixed inset-0 z-[9998] flex items-center justify-center p-4" @click.self="$emit('cancel')">
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm"></div>
        <div
          class="relative bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md border border-slate-200"
          :dir="direction"
          role="dialog"
          aria-modal="true"
          :aria-label="title"
        >
          <div class="flex items-center gap-3 mb-4">
            <span v-html="icon" class="shrink-0" :class="iconClass"></span>
            <h3 class="text-lg font-bold text-slate-800">{{ title }}</h3>
          </div>
          <p class="text-slate-600 text-sm mb-6 leading-relaxed">{{ message }}</p>
          <div class="flex gap-3">
            <button
              ref="confirmBtn"
              @click="$emit('confirm')"
              class="flex-1 py-2.5 rounded-lg text-sm font-medium text-white transition-colors"
              :class="confirmClass"
            >
              {{ confirmText }}
            </button>
            <button
              @click="$emit('cancel')"
              class="flex-1 py-2.5 rounded-lg text-sm font-medium bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors"
            >
              {{ cancelText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { ICONS } from '../composables/useIcons'
import { L, useLocale } from '../composables/useLocale'

const { direction } = useLocale()

const props = defineProps({
  visible: Boolean,
  title: { type: String, default: () => L.actions.confirm },
  message: { type: String, default: () => L.actions.confirmMessage },
  confirmText: { type: String, default: () => L.actions.confirm },
  cancelText: { type: String, default: () => L.actions.cancel },
  variant: { type: String, default: 'danger' },
})

defineEmits(['confirm', 'cancel'])

const confirmBtn = ref(null)

watch(() => props.visible, async (v) => {
  if (v) {
    await nextTick()
    confirmBtn.value?.focus()
  }
})

const icon = ICONS.alert
const iconClass = props.variant === 'danger' ? 'text-red-500' : 'text-blue-500'
const confirmClass = props.variant === 'danger'
  ? 'bg-red-600 hover:bg-red-700'
  : 'bg-blue-900 hover:bg-blue-800'
</script>

<style scoped>
.dialog-enter-active { transition: all 0.2s ease-out; }
.dialog-leave-active { transition: all 0.15s ease-in; }
.dialog-enter-from { opacity: 0; }
.dialog-enter-from > div:last-child { transform: scale(0.95); }
.dialog-leave-to { opacity: 0; }
</style>
