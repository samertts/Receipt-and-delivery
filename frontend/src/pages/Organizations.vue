<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold text-slate-800">{{ L.org.title }}</h1>
      <button
        v-if="auth.isAdmin || auth.userRole === 'supervisor'"
        @click="showForm = true"
        class="gov-btn-primary"
      >
        <span v-html="ICONS.plus"></span>
        {{ L.org.add }}
      </button>
    </div>

    <div
      v-if="error"
      class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-3"
    >
      <span v-html="ICONS.alert"></span>
      <span>{{ error }}</span>
      <button @click="fetchData" class="mr-auto text-red-600 hover:text-red-800 font-medium">
        {{ L.actions.retry }}
      </button>
    </div>

    <DataTable
      v-else
      :columns="columns"
      :rows="items"
      :loading="loading"
      row-key="id"
      default-sort="name"
    >
      <template #empty>
        <div class="flex flex-col items-center gap-2">
          <span class="text-slate-300 text-4xl" v-html="ICONS.organizations"></span>
          <p class="text-sm">{{ L.org.noOrgs }}</p>
        </div>
      </template>

      <template #cell-code="{ value }">
        <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-xs font-mono">{{ value }}</span>
      </template>

      <template #cell-phone="{ value }">
        {{ value || '-' }}
      </template>

      <template #cell-email="{ value }">
        {{ value || '-' }}
      </template>
    </DataTable>

    <ModalDialog
      :visible="showForm"
      :title="L.org.new"
      size="md"
      @close="closeForm"
    >
      <div
        v-if="formError"
        class="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg mb-4 flex items-center gap-2"
      >
        <span v-html="ICONS.alert"></span>
        <span>{{ formError }}</span>
      </div>

      <div class="space-y-3">
        <div>
          <input
            v-model="newOrg.name"
            :placeholder="L.org.name"
            class="gov-input"
            :class="{ 'border-red-400': validationErrors.name }"
          />
          <p v-if="validationErrors.name" class="text-red-500 text-xs mt-1">{{ validationErrors.name }}</p>
        </div>
        <div>
          <input
            v-model="newOrg.code"
            :placeholder="L.org.code"
            class="gov-input"
            :class="{ 'border-red-400': validationErrors.code }"
          />
          <p v-if="validationErrors.code" class="text-red-500 text-xs mt-1">{{ validationErrors.code }}</p>
        </div>
        <input v-model="newOrg.address" :placeholder="L.org.governorate" class="gov-input" />
        <input v-model="newOrg.phone" :placeholder="L.org.phone" class="gov-input" type="tel" />
        <input v-model="newOrg.email" :placeholder="L.org.email" class="gov-input" type="email" />
      </div>

      <template #footer>
        <button
          @click="createOrg"
          :disabled="submitting"
          class="gov-btn-primary flex-1"
        >
          <span
            v-if="submitting"
            class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
          ></span>
          <span v-else>{{ submitting ? L.actions.loading : L.actions.save }}</span>
        </button>
        <button @click="closeForm" class="gov-btn-secondary flex-1">{{ L.actions.cancel }}</button>
      </template>
    </ModalDialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useUiStore } from '../stores/ui'
import { organizationsApi } from '../api'
import { ICONS } from '../composables/useIcons'
import { L } from '../composables/useLocale'
import DataTable from '../components/DataTable.vue'
import ModalDialog from '../components/ModalDialog.vue'

const auth = useAuthStore()
const ui = useUiStore()

const items = ref([])
const loading = ref(true)
const error = ref(null)
const showForm = ref(false)
const submitting = ref(false)
const formError = ref(null)
const validationErrors = ref({})
const newOrg = ref({ name: '', code: '', address: '', phone: '', email: '' })

const columns = [
  { key: 'name', label: L.org.nameLabel, sortable: true },
  { key: 'code', label: L.org.code, sortable: true },
  { key: 'phone', label: L.org.phoneLabel },
  { key: 'email', label: L.org.emailLabel },
  { key: 'address', label: L.org.governorate, sortable: true },
]

function validate() {
  const errors = {}
  if (!newOrg.value.name?.trim()) errors.name = 'هذا الحقل مطلوب'
  if (!newOrg.value.code?.trim()) errors.code = 'هذا الحقل مطلوب'
  validationErrors.value = errors
  return Object.keys(errors).length === 0
}

function closeForm() {
  showForm.value = false
  formError.value = null
  validationErrors.value = {}
  newOrg.value = { name: '', code: '', address: '', phone: '', email: '' }
}

async function fetchData() {
  loading.value = true
  error.value = null
  try {
    const res = await organizationsApi.list()
    items.value = res.data
  } catch (e) {
    error.value = L.errors.loadFailedOrgs
  } finally {
    loading.value = false
  }
}

async function createOrg() {
  if (!validate()) return
  submitting.value = true
  formError.value = null
  try {
    await organizationsApi.create(newOrg.value)
    closeForm()
    newOrg.value = { name: '', code: '', address: '', phone: '', email: '' }
    ui.success(L.org.created)
    await fetchData()
  } catch (e) {
    formError.value = e.response?.data?.detail || L.errors.saveFailed
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>

<style scoped>
.dialog-enter-active { transition: all 0.2s ease-out; }
.dialog-leave-active { transition: all 0.15s ease-in; }
.dialog-enter-from, .dialog-leave-to { opacity: 0; }
.dialog-enter-from > div:last-child { transform: scale(0.95); }
</style>
