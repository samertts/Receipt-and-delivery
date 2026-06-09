import { defineStore } from 'pinia'
import { ref } from 'vue'

let toastId = 0

export const useUiStore = defineStore('ui', () => {
  const toasts = ref([])
  const sidebarCollapsed = ref(false)

  function addToast(message, type = 'info', duration = 4000) {
    const id = ++toastId
    toasts.value.push({ id, message, type })
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
    return id
  }

  function removeToast(id) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function success(message) { return addToast(message, 'success') }
  function error(message) { return addToast(message, 'error', 6000) }
  function info(message) { return addToast(message, 'info') }
  function warning(message) { return addToast(message, 'warning', 5000) }

  return { toasts, sidebarCollapsed, addToast, removeToast, toggleSidebar, success, error, info, warning }
})
