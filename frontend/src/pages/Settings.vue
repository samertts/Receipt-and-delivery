<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">{{ L.settings.title }}</h1>

    <div v-if="!auth.isAdmin" class="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-lg flex items-center gap-2">
      <span v-html="icons.alert"></span>
      <span>{{ L.settings.noPermission }}</span>
    </div>

    <div v-else class="space-y-6">
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
          <span class="text-slate-600" v-html="icons.users"></span>
          {{ L.settings.userManagement }}
        </h2>

        <DataTable
          :columns="columns"
          :rows="users"
          :loading="usersLoading"
          row-key="id"
        >
          <template #cell-role="{ value }">
            <span class="gov-badge" :class="roleBadgeClass(value)">{{ L.roles[value] || value }}</span>
          </template>
          <template #cell-status="{ value }">
            <span class="gov-badge" :class="statusBadgeClass(value)">{{ L.status[value] || value }}</span>
          </template>
        </DataTable>

        <details class="border border-slate-200 rounded-xl overflow-hidden mt-4">
          <summary class="cursor-pointer text-sm font-medium text-blue-700 px-4 py-3 hover:bg-blue-50 transition-colors">
            {{ L.settings.addUser }}
          </summary>
          <div class="p-4 space-y-3 border-t border-slate-200">
            <div v-if="userError" class="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg flex items-center gap-2">
              <span v-html="icons.alert"></span>
              <span>{{ userError }}</span>
            </div>
            <div v-if="userSuccess" class="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm p-3 rounded-lg flex items-center gap-2">
              <span v-html="icons.check"></span>
              <span>{{ userSuccess }}</span>
            </div>
            <input v-model="newUser.username" :placeholder="L.settings.username" class="gov-input" />
            <input v-model="newUser.full_name" :placeholder="L.settings.fullName" class="gov-input" />
            <input v-model="newUser.password" type="password" :placeholder="L.settings.password" class="gov-input" />
            <select v-model="newUser.role" class="gov-select">
              <option v-for="(label, key) in L.roles" :key="key" :value="key">{{ label }}</option>
            </select>
            <button @click="createUser" :disabled="userSubmitting" class="gov-btn-primary">
              <span v-if="userSubmitting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span>{{ userSubmitting ? L.actions.loading : L.actions.save }}</span>
            </button>
          </div>
        </details>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { usersApi } from '../api'
import { ICONS } from '../composables/useIcons'
import { L } from '../composables/useLocale'
import DataTable from '../components/DataTable.vue'

const auth = useAuthStore()
const icons = ICONS

const columns = [
  { key: 'username', label: L.settings.username, sortable: true },
  { key: 'full_name', label: L.settings.fullName, sortable: true },
  { key: 'role', label: L.settings.role, sortable: true },
  { key: 'status', label: L.settings.status, sortable: true },
]

const users = ref([])
const usersLoading = ref(true)
const userError = ref(null)
const userSuccess = ref(null)
const userSubmitting = ref(false)
const newUser = ref({ username: '', full_name: '', password: '', role: 'user' })

function roleBadgeClass(role) {
  const map = {
    admin: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200',
    supervisor: 'bg-purple-50 text-purple-700 ring-1 ring-purple-200',
    auditor: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
    user: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
  }
  return map[role] || map.user
}

function statusBadgeClass(status) {
  return status === 'active'
    ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200'
    : 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
}

async function fetchUsers() {
  usersLoading.value = true
  try {
    const res = await usersApi.list()
    users.value = res.data
  } catch (e) {
    // ignore
  } finally {
    usersLoading.value = false
  }
}

async function createUser() {
  userSubmitting.value = true
  userError.value = null
  userSuccess.value = null
  try {
    await usersApi.create(newUser.value)
    userSuccess.value = L.settings.userCreated
    newUser.value = { username: '', full_name: '', password: '', role: 'user' }
    await fetchUsers()
  } catch (e) {
    userError.value = e.response?.data?.detail || 'فشل في إنشاء المستخدم'
  } finally {
    userSubmitting.value = false
  }
}

onMounted(fetchUsers)
</script>
