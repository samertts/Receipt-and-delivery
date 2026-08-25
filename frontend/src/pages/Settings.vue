<template>
  <div :dir="direction">
    <h1 class="text-2xl font-bold text-slate-800 mb-6">{{ L.settings.title }}</h1>

    <div v-if="!auth.hasPermission('manage_users')" class="bg-amber-50 border border-amber-200 text-amber-700 p-4 rounded-lg flex items-center gap-2">
      <span v-html="icons.alert"></span>
      <span>{{ L.settings.noPermission }}</span>
    </div>

    <div v-else class="space-y-6">
      <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-4">
          <h2 class="text-lg font-semibold flex items-center gap-2">
            <span class="text-slate-600" v-html="icons.users"></span>
            {{ L.settings.userManagement }}
          </h2>
          <div class="flex flex-col sm:flex-row gap-2">
            <select v-model="filters.role" class="gov-select" @change="fetchUsers">
              <option value="">{{ L.settings.allRoles }}</option>
              <option v-for="role in roleOptions" :key="role" :value="role">{{ L.roles[role] }}</option>
            </select>
            <select v-model="filters.status" class="gov-select" @change="fetchUsers">
              <option value="">{{ L.settings.allStatuses }}</option>
              <option value="active">{{ L.status.active }}</option>
              <option value="inactive">{{ L.status.inactive }}</option>
            </select>
          </div>
        </div>

        <DataTable :columns="columns" :rows="users" :loading="usersLoading" row-key="id">
          <template #cell-role="{ value }">
            <span class="gov-badge" :class="roleBadgeClass(value)">{{ L.roles[value] || value }}</span>
          </template>
          <template #cell-status="{ value }">
            <span class="gov-badge" :class="statusBadgeClass(value)">{{ L.status[value] || value }}</span>
          </template>
          <template #cell-actions="{ row }">
            <div class="flex items-center justify-end gap-2" @click.stop>
              <button type="button" class="text-blue-600 hover:text-blue-800 text-xs font-medium" @click="openEdit(row)">{{ L.actions.edit }}</button>
              <button
                type="button"
                class="text-xs font-medium"
                :class="row.status === 'active' ? 'text-red-600 hover:text-red-800' : 'text-emerald-600 hover:text-emerald-800'"
                :disabled="row.id === auth.user?.id || row.username === auth.user?.username"
                @click="toggleStatus(row)"
              >{{ row.status === 'active' ? L.settings.deactivate : L.settings.activate }}</button>
            </div>
          </template>
        </DataTable>
      </section>

      <section v-if="editingUser" class="bg-white rounded-xl shadow-sm border border-blue-200 p-6">
        <h2 class="text-lg font-semibold mb-4">{{ L.settings.editUser }}: {{ editingUser.username }}</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input v-model="editForm.full_name" :placeholder="L.settings.fullName" class="gov-input" />
          <select v-model="editForm.role" class="gov-select">
            <option v-for="role in roleOptions" :key="role" :value="role">{{ L.roles[role] }}</option>
          </select>
          <select v-model="editForm.status" class="gov-select">
            <option value="active">{{ L.status.active }}</option>
            <option value="inactive">{{ L.status.inactive }}</option>
          </select>
        </div>
        <div class="flex gap-2 mt-4">
          <button type="button" class="gov-btn-primary" :disabled="userSubmitting" @click="saveUser">{{ userSubmitting ? L.actions.loading : L.settings.saveChanges }}</button>
          <button type="button" class="gov-btn-secondary" @click="editingUser = null">{{ L.actions.cancel }}</button>
        </div>
      </section>

      <details class="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <summary class="cursor-pointer text-sm font-medium text-blue-700 px-4 py-3 hover:bg-blue-50 transition-colors">{{ L.settings.addUser }}</summary>
        <div class="p-4 space-y-3 border-t border-slate-200">
          <div v-if="userError" class="bg-red-50 border border-red-200 text-red-700 text-sm p-3 rounded-lg" role="alert">{{ userError }}</div>
          <div v-if="userSuccess" class="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm p-3 rounded-lg" role="status">{{ userSuccess }}</div>
          <input v-model="newUser.username" :placeholder="L.settings.username" class="gov-input" />
          <input v-model="newUser.full_name" :placeholder="L.settings.fullName" class="gov-input" />
          <input v-model="newUser.password" type="password" :placeholder="L.settings.password" class="gov-input" />
          <select v-model="newUser.role" class="gov-select">
            <option v-for="role in roleOptions" :key="role" :value="role">{{ L.roles[role] }}</option>
          </select>
          <button type="button" @click="createUser" :disabled="userSubmitting" class="gov-btn-primary">
            <span v-if="userSubmitting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span>{{ userSubmitting ? L.actions.loading : L.actions.save }}</span>
          </button>
        </div>
      </details>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '../stores/auth'
import { usersApi } from '../api'
import { ICONS } from '../composables/useIcons'
import { L, useLocale } from '../composables/useLocale'
import DataTable from '../components/DataTable.vue'

const auth = useAuthStore()
const icons = ICONS
const { direction } = useLocale()
const roleOptions = ['admin', 'supervisor', 'user', 'auditor']
const filters = ref({ role: '', status: '' })
const users = ref([])
const usersLoading = ref(true)
const userError = ref(null)
const userSuccess = ref(null)
const userSubmitting = ref(false)
const editingUser = ref(null)
const newUser = ref({ username: '', full_name: '', password: '', role: 'user' })
const editForm = ref({ full_name: '', role: 'user', status: 'active' })

const columns = computed(() => [
  { key: 'username', label: L.settings.username, sortable: true },
  { key: 'full_name', label: L.settings.fullName, sortable: true },
  { key: 'role', label: L.settings.role, sortable: true },
  { key: 'status', label: L.settings.status, sortable: true },
  { key: 'actions', label: L.actions.edit, sortable: false, align: 'left' },
])

function roleBadgeClass(role) {
  const map = { admin: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200', supervisor: 'bg-purple-50 text-purple-700 ring-1 ring-purple-200', auditor: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200', user: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200' }
  return map[role] || map.user
}

function statusBadgeClass(status) {
  return status === 'active' ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200' : 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
}

async function fetchUsers() {
  usersLoading.value = true
  userError.value = null
  try {
    const response = await usersApi.list({ ...filters.value, page: 1, limit: 100 })
    users.value = Array.isArray(response.data) ? response.data : response.data?.items || []
  } catch (error) {
    userError.value = error.apiMessage || L.errors.loadFailed
  } finally {
    usersLoading.value = false
  }
}

function openEdit(user) {
  editingUser.value = user
  editForm.value = { full_name: user.full_name || '', role: user.role, status: user.status || 'active' }
  userError.value = null
  userSuccess.value = null
}

async function saveUser() {
  if (!editingUser.value) return
  userSubmitting.value = true
  userError.value = null
  userSuccess.value = null
  try {
    await usersApi.update(editingUser.value.id, editForm.value)
    userSuccess.value = L.settings.userUpdated
    editingUser.value = null
    await fetchUsers()
  } catch (error) {
    userError.value = error.apiMessage || error.response?.data?.detail || L.errors.updateFailed
  } finally {
    userSubmitting.value = false
  }
}

async function toggleStatus(user) {
  if (user.id === auth.user?.id || user.username === auth.user?.username) {
    userError.value = L.settings.cannotDeactivateSelf
    return
  }
  editingUser.value = user
  editForm.value = { full_name: user.full_name || '', role: user.role, status: user.status === 'active' ? 'inactive' : 'active' }
  await saveUser()
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
  } catch (error) {
    userError.value = error.apiMessage || error.response?.data?.detail || L.errors.saveFailed
  } finally {
    userSubmitting.value = false
  }
}

onMounted(fetchUsers)
</script>
