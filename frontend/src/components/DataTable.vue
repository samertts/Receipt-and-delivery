<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="overflow-x-auto">
      <table class="w-full text-sm" role="table">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200">
            <th
              v-for="col in columns"
              :key="col.key"
              @click="col.sortable !== false ? toggleSort(col.key) : undefined"
              :class="[
                'py-3 px-4 font-medium text-slate-600 text-right',
                col.align === 'center' ? 'text-center' : col.align === 'left' ? 'text-left' : 'text-right',
                col.sortable !== false ? 'cursor-pointer hover:text-slate-800 select-none' : '',
              ]"
              :style="col.width ? { width: col.width } : {}"
              :aria-sort="sortKey === col.key ? (sortOrder === 'asc' ? 'ascending' : 'descending') : 'none'"
              :tabindex="col.sortable !== false ? 0 : -1"
              @keydown.enter="col.sortable !== false ? toggleSort(col.key) : undefined"
              @keydown.space.prevent="col.sortable !== false ? toggleSort(col.key) : undefined"
            >
              <div class="flex items-center gap-1" :class="col.align === 'center' ? 'justify-center' : col.align === 'left' ? 'justify-start' : 'justify-end'">
                <span>{{ col.label }}</span>
                <span v-if="sortKey === col.key" class="shrink-0 text-slate-400" v-html="sortOrder === 'asc' ? icons.sortAsc : icons.sortDesc"></span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody v-if="loading">
          <tr v-for="i in skeletonRows" :key="i">
            <td v-for="col in columns" :key="col.key" class="py-3 px-4">
              <div class="skeleton h-5 w-full" :style="{ maxWidth: col.skeletonWidth || '80%' }"></div>
            </td>
          </tr>
        </tbody>
        <tbody v-else-if="rows.length === 0">
          <tr>
            <td :colspan="columns.length" class="text-center py-12 text-slate-400">
              <slot name="empty">
                <div class="flex flex-col items-center gap-2">
                  <span class="text-slate-300 text-4xl" v-html="icons.empty"></span>
                  <p class="text-sm">لا توجد بيانات</p>
                </div>
              </slot>
            </td>
          </tr>
        </tbody>
        <tbody v-else>
          <tr
            v-for="(row, idx) in sortedRows"
            :key="rowKey ? row[rowKey] : idx"
            @click="$emit('row-click', row)"
            :class="[
              'border-b border-slate-100 transition-colors',
              clickable ? 'cursor-pointer hover:bg-blue-50' : 'hover:bg-slate-50',
            ]"
            :tabindex="clickable ? 0 : -1"
            @keydown.enter="clickable ? $emit('row-click', row) : undefined"
            @keydown.space.prevent="clickable ? $emit('row-click', row) : undefined"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="[
                'py-3 px-4',
                col.align === 'center' ? 'text-center' : col.align === 'left' ? 'text-left' : 'text-right',
              ]"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="getNestedValue(row, col.key)">
                <span v-if="col.badge" :class="col.badge(row)" class="gov-badge">{{ formatCell(row, col) }}</span>
                <span v-else>{{ formatCell(row, col) }}</span>
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed, shallowRef } from 'vue'
import { ICONS } from '../composables/useIcons'

const props = defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  rowKey: { type: String, default: null },
  clickable: { type: Boolean, default: false },
  skeletonRows: { type: Number, default: 5 },
  defaultSort: { type: String, default: null },
  defaultSortOrder: { type: String, default: 'asc' },
})

defineEmits(['row-click', 'sort-change'])

const icons = ICONS
const sortKey = shallowRef(props.defaultSort)
const sortOrder = shallowRef(props.defaultSortOrder)

const EMPTY_ICON = `<svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`
icons.empty = EMPTY_ICON

const SORT_ASC = `<svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="19 12 12 19 5 12"/></svg>`
const SORT_DESC = `<svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><polyline points="5 12 12 5 19 12"/></svg>`
icons.sortAsc = SORT_ASC
icons.sortDesc = SORT_DESC

function getNestedValue(obj, path) {
  return path.split('.').reduce((acc, part) => acc?.[part], obj)
}

function formatCell(row, col) {
  const val = getNestedValue(row, col.key)
  if (col.format) return col.format(val, row)
  if (val === null || val === undefined) return '-'
  return val
}

function toggleSort(key) {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = 'asc'
  }
}

const sortedRows = computed(() => {
  if (!sortKey.value) return props.rows
  const key = sortKey.value
  const order = sortOrder.value
  const col = props.columns.find((c) => c.key === key)
  if (col?.sortable === false) return props.rows

  return [...props.rows].sort((a, b) => {
    let va = getNestedValue(a, key)
    let vb = getNestedValue(b, key)
    if (va === null || va === undefined) return 1
    if (vb === null || vb === undefined) return -1
    if (typeof va === 'number' && typeof vb === 'number') {
      return order === 'asc' ? va - vb : vb - va
    }
    va = String(va)
    vb = String(vb)
    return order === 'asc' ? va.localeCompare(vb, 'ar') : vb.localeCompare(va, 'ar')
  })
})
</script>
