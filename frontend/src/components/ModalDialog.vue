<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="fixed inset-0 z-[9998] flex items-center justify-center p-4"
        role="dialog"
        :aria-modal="true"
        :aria-label="title"
      >
        <div class="fixed inset-0 bg-black/40 backdrop-blur-sm" @click="closeOnBackdrop ? $emit('close') : undefined"></div>
        <div
          ref="modalRef"
          class="relative bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col max-h-[90vh]"
          :class="sizeClass"
          dir="rtl"
        >
          <div v-if="title" class="flex items-center justify-between px-6 py-4 border-b border-slate-200 shrink-0">
            <h2 class="text-lg font-semibold text-slate-800">{{ title }}</h2>
            <button
              @click="$emit('close')"
              class="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100 transition-colors"
              aria-label="إغلاق"
            >
              <span v-html="icons.close"></span>
            </button>
          </div>
          <div class="overflow-y-auto p-6">
            <slot />
          </div>
          <div v-if="$slots.footer" class="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-200 shrink-0">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { ICONS } from '../composables/useIcons'

const props = defineProps({
  visible: Boolean,
  title: { type: String, default: '' },
  size: { type: String, default: 'md' },
  closeOnBackdrop: { type: Boolean, default: true },
})

defineEmits(['close'])

const icons = ICONS
const modalRef = ref(null)

const sizeMap = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
  full: 'max-w-6xl',
}

const sizeClass = sizeMap[props.size] || sizeMap.md

watch(() => props.visible, async (v) => {
  if (v) {
    document.body.style.overflow = 'hidden'
    await nextTick()
    trapFocus()
  } else {
    document.body.style.overflow = ''
  }
})

function trapFocus() {
  if (!modalRef.value) return
  const focusable = modalRef.value.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])')
  if (focusable.length) focusable[0].focus()
}
</script>

<style scoped>
.modal-enter-active { transition: all 0.2s ease-out; }
.modal-leave-active { transition: all 0.15s ease-in; }
.modal-enter-from { opacity: 0; }
.modal-enter-from > div:last-child { transform: scale(0.95) translateY(10px); }
.modal-leave-to { opacity: 0; }
.modal-leave-to > div:last-child { transform: scale(0.95); }
</style>
