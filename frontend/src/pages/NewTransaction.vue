<template>
  <div>
    <h1 class="text-2xl font-bold text-slate-800 mb-6">معاملة جديدة</h1>

    <div v-if="loading" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div class="space-y-4">
        <div v-for="i in 4" :key="i" class="skeleton h-10 w-full"></div>
        <div class="skeleton h-32 w-full"></div>
      </div>
    </div>

    <form v-else @submit.prevent="submitForm" class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      <div v-if="error" class="bg-red-50 border border-red-200 text-red-700 text-sm p-4 rounded-lg flex items-center gap-2">
        <span v-html="icons.alert"></span>
        <span>{{ error }}</span>
      </div>
      <div v-if="success" class="bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm p-4 rounded-lg flex items-center gap-2">
        <span v-html="icons.check"></span>
        <span>تم إنشاء المعاملة بنجاح: {{ success }}</span>
        <router-link to="/transactionslist" class="mr-auto text-emerald-700 hover:text-emerald-900 font-medium underline">
          العودة إلى القائمة
        </router-link>
      </div>

      <div v-if="!success" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="md:col-span-2">
          <label class="gov-label">نوع المعاملة</label>
          <select v-model="form.transaction_type" required class="gov-select">
            <option value="">اختر نوع المعاملة...</option>
            <option value="استلام عينات">استلام عينات</option>
            <option value="تسليم عينات">تسليم عينات</option>
            <option value="تحويل مختبري">تحويل مختبري</option>
            <option value="إعادة عينات">إعادة عينات</option>
            <option value="تسليم نتائج">تسليم نتائج</option>
            <option value="أخرى">أخرى</option>
          </select>
        </div>
        <div>
          <label class="gov-label">تاريخ المعاملة</label>
          <input v-model="form.transaction_date" type="date" required class="gov-input" />
        </div>
        <div>
          <label class="gov-label">المرسل</label>
          <input v-model="form.sender_name" required placeholder="اسم المرسل" class="gov-input" />
        </div>
        <div>
          <label class="gov-label">المستلم</label>
          <input v-model="form.receiver_name" required placeholder="اسم المستلم" class="gov-input" />
        </div>
        <div>
          <label class="gov-label">المنشأة المرسلة</label>
          <div class="relative">
            <input
              v-model="senderOrgSearch"
              @focus="senderDropdownOpen = true"
              @input="senderDropdownOpen = true"
              placeholder="ابحث عن منشأة..."
              class="gov-input"
            />
            <ul v-if="senderDropdownOpen && filteredSenderOrgs.length"
              class="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-40 overflow-y-auto"
            >
              <li v-for="org in filteredSenderOrgs" :key="org.id"
                @click="selectSenderOrg(org)"
                class="px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm"
              >
                {{ org.name }} <span class="text-slate-400">({{ org.code }})</span>
              </li>
            </ul>
          </div>
        </div>
        <div>
          <label class="gov-label">المنشأة المستلمة</label>
          <div class="relative">
            <input
              v-model="receiverOrgSearch"
              @focus="receiverDropdownOpen = true"
              @input="receiverDropdownOpen = true"
              placeholder="ابحث عن منشأة..."
              class="gov-input"
            />
            <ul v-if="receiverDropdownOpen && filteredReceiverOrgs.length"
              class="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-40 overflow-y-auto"
            >
              <li v-for="org in filteredReceiverOrgs" :key="org.id"
                @click="selectReceiverOrg(org)"
                class="px-4 py-2 hover:bg-blue-50 cursor-pointer text-sm"
              >
                {{ org.name }} <span class="text-slate-400">({{ org.code }})</span>
              </li>
            </ul>
          </div>
        </div>
        <div>
          <label class="gov-label">رقم التفويض</label>
          <input v-model="form.authorization_no" class="gov-input" />
        </div>
        <div>
          <label class="gov-label">تاريخ التفويض</label>
          <input v-model="form.authorization_date" type="date" class="gov-input" />
        </div>
        <div class="md:col-span-2">
          <label class="gov-label">ملاحظات</label>
          <textarea v-model="form.notes" rows="3" class="gov-input" placeholder="ملاحظات إضافية..."></textarea>
        </div>
      </div>

      <div v-if="!success">
        <div class="flex items-center justify-between mb-3">
          <h2 class="text-lg font-semibold text-slate-800">بنود المعاملة</h2>
          <button type="button" @click="addItem" class="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1">
            <span v-html="icons.plus"></span> إضافة بند
          </button>
        </div>
        <div v-for="(item, idx) in form.items" :key="idx"
          class="bg-slate-50 rounded-lg p-4 mb-3 border border-slate-200"
        >
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="relative">
              <label class="block text-xs text-slate-500 mb-1">نوع العينة</label>
              <div class="relative">
                <input
                  v-model="item.sample_type"
                  @focus="sampleDropdownIdx = idx"
                  @input="sampleDropdownIdx = idx"
                  required placeholder="اختر أو اكتب..."
                  class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm"
                />
                <ul v-if="sampleDropdownIdx === idx && filteredSampleTypes.length"
                  class="absolute z-10 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-32 overflow-y-auto"
                >
                  <li v-for="st in filteredSampleTypes" :key="st"
                    @click="selectSampleType(idx, st)"
                    class="px-3 py-1.5 hover:bg-blue-50 cursor-pointer text-sm"
                  >{{ st }}</li>
                </ul>
              </div>
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">المجموع</label>
              <input v-model.number="item.total_count" type="number" min="1" required class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">صالح</label>
              <input v-model.number="item.valid_count" type="number" min="0" required class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">تالف</label>
              <input v-model.number="item.damaged_count" type="number" min="0" required class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">مرفوض</label>
              <input v-model.number="item.rejected_count" type="number" min="0" required class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">غير مطابق</label>
              <input v-model.number="item.nonconforming_count" type="number" min="0" required class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm" />
            </div>
            <div>
              <label class="block text-xs text-slate-500 mb-1">حالة النقل</label>
              <select v-model="item.transport_condition" class="w-full px-3 py-1.5 border border-slate-300 rounded text-sm bg-white">
                <option value="">اختر...</option>
                <option value="جيدة">جيدة</option>
                <option value="متوسطة">متوسطة</option>
                <option value="سيئة">سيئة</option>
              </select>
            </div>
            <div class="flex items-end">
              <button type="button" @click="removeItem(idx)" class="text-red-500 text-sm hover:text-red-700 flex items-center gap-1">
                <span v-html="icons.close"></span> حذف
              </button>
            </div>
          </div>
        </div>
      </div>

      <button v-if="!success" type="submit" :disabled="submitting"
        class="w-full bg-primary-900 text-white py-2.5 rounded-lg font-medium hover:bg-primary-800 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
      >
        <span v-if="submitting" class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
        <span>{{ submitting ? 'جاري الحفظ...' : 'حفظ المعاملة' }}</span>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { transactionsApi, organizationsApi } from '../api'
import { useUiStore } from '../stores/ui'
import { ICONS } from '../composables/useIcons'

const ui = useUiStore()
const icons = ICONS

const loading = ref(false)
const submitting = ref(false)
const error = ref(null)
const success = ref(null)

const organizations = ref([])
const sampleTypes = [
  'Serum', 'Plasma', 'Whole Blood', 'Urine', 'Stool',
  'Sputum', 'CSF', 'Swab', 'Tissue', 'Water', 'Food', 'Other',
]

const senderOrgSearch = ref('')
const receiverOrgSearch = ref('')
const senderDropdownOpen = ref(false)
const receiverDropdownOpen = ref(false)
const sampleDropdownIdx = ref(-1)

const filteredSenderOrgs = computed(() =>
  organizations.value.filter((o) =>
    o.name.includes(senderOrgSearch.value) || o.code.includes(senderOrgSearch.value)
  )
)
const filteredReceiverOrgs = computed(() =>
  organizations.value.filter((o) =>
    o.name.includes(receiverOrgSearch.value) || o.code.includes(receiverOrgSearch.value)
  )
)
const filteredSampleTypes = computed(() =>
  sampleTypes.filter((s) =>
    s.toLowerCase().includes(
      (form.value.items[sampleDropdownIdx.value]?.sample_type || '').toLowerCase()
    )
  )
)

async function loadOrganizations() {
  try {
    const response = await organizationsApi.list()
    organizations.value = response.data
  } catch {
    // silently fail; user can still type org ID
  }
}

function selectSenderOrg(org) {
  form.value.sender_organization_id = org.id
  senderOrgSearch.value = `${org.name} (${org.code})`
  senderDropdownOpen.value = false
}
function selectReceiverOrg(org) {
  form.value.receiver_organization_id = org.id
  receiverOrgSearch.value = `${org.name} (${org.code})`
  receiverDropdownOpen.value = false
}
function selectSampleType(idx, st) {
  form.value.items[idx].sample_type = st
  sampleDropdownIdx.value = -1
}

document.addEventListener('click', (e) => {
  if (!e.target.closest('.relative')) {
    senderDropdownOpen.value = false
    receiverDropdownOpen.value = false
    sampleDropdownIdx.value = -1
  }
})

function resetForm() {
  form.value = {
    transaction_type: '',
    transaction_date: new Date().toISOString().split('T')[0],
    sender_name: '',
    receiver_name: '',
    sender_organization_id: '',
    receiver_organization_id: '',
    authorization_no: '',
    authorization_date: '',
    notes: '',
    status: 'draft',
    items: [
      { sample_type: '', total_count: 1, valid_count: 1, damaged_count: 0, rejected_count: 0, nonconforming_count: 0, transport_condition: '', notes: '' },
    ],
  }
  senderOrgSearch.value = ''
  receiverOrgSearch.value = ''
}

const form = ref({
  transaction_type: '',
  transaction_date: new Date().toISOString().split('T')[0],
  sender_name: '',
  receiver_name: '',
  sender_organization_id: '',
  receiver_organization_id: '',
  authorization_no: '',
  authorization_date: '',
  notes: '',
  status: 'draft',
  items: [
    { sample_type: '', total_count: 1, valid_count: 1, damaged_count: 0, rejected_count: 0, nonconforming_count: 0, transport_condition: '', notes: '' },
  ],
})

function addItem() {
  form.value.items.push({ sample_type: '', total_count: 1, valid_count: 0, damaged_count: 0, rejected_count: 0, nonconforming_count: 0, transport_condition: '', notes: '' })
}

function removeItem(idx) {
  if (form.value.items.length > 1) {
    form.value.items.splice(idx, 1)
  }
}

async function submitForm() {
  submitting.value = true
  error.value = null
  success.value = null
  try {
    const result = await transactionsApi.create(form.value)
    success.value = result.data.transaction_no
    ui.success(`تم إنشاء المعاملة ${result.data.transaction_no} بنجاح`)
    resetForm()
  } catch (e) {
    error.value = e.response?.data?.detail || 'فشل في إنشاء المعاملة'
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  loading.value = false
  loadOrganizations()
})
</script>
