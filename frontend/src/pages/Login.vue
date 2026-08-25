<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-slate-100 p-4" :dir="direction">
    <button type="button" class="fixed top-4 right-4 gov-btn-secondary" @click="toggleLocale">{{ locale === 'ar' ? L.switchToEnglish : L.switchToArabic }}</button>
    <div class="w-full max-w-md">
      <div class="bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
        <div class="text-center mb-8">
          <div class="w-16 h-16 bg-primary-900 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <span class="text-white text-2xl font-bold">م</span>
          </div>
          <h1 class="text-2xl font-bold text-primary-900">{{ L.appFullName }}</h1>
          <p class="text-slate-500 mt-2 text-sm">{{ L.auth.loginTitle }}</p>
        </div>
        <form @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label class="gov-label" for="username">{{ L.auth.username }}</label>
            <input
              id="username"
              v-model="username"
              type="text"
              required
              class="gov-input"
              :placeholder="L.auth.usernamePlaceholder"
              :disabled="loading"
              autocomplete="username"
            />
          </div>
          <div>
            <label class="gov-label" for="password">{{ L.auth.password }}</label>
            <input
              id="password"
              v-model="password"
              type="password"
              required
              class="gov-input"
              :placeholder="L.auth.passwordPlaceholder"
              :disabled="loading"
              autocomplete="current-password"
            />
          </div>
          <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg flex items-center gap-2">
            <span v-html="icons.alert"></span>
            <span>{{ error }}</span>
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full bg-primary-900 text-white py-2.5 rounded-lg font-medium hover:bg-primary-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <span v-if="loading" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span>{{ loading ? L.auth.loggingIn : L.auth.login }}</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ICONS } from '../composables/useIcons'
import { L, useLocale } from '../composables/useLocale'

const router = useRouter()
const auth = useAuthStore()
const icons = ICONS
const { locale, direction, toggleLocale } = useLocale()

const username = ref('')
const password = ref('')
const error = ref(null)
const loading = ref(false)

async function handleLogin() {
  error.value = null
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.apiMessage || e.response?.data?.message || e.response?.data?.detail || L.auth.loginFailed
  } finally {
    loading.value = false
  }
}
</script>
