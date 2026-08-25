import { computed, ref, watch } from 'vue'

const AR = {
  language: 'اللغة',
  arabic: 'العربية',
  english: 'English',
  switchToEnglish: 'English',
  switchToArabic: 'العربية',
  appName: 'الاستلام المختبري',
  appSubtitle: 'نظام الاستلام والتسليم المختبري',
  appFullName: 'نظام إدارة الاستلام المختبري',
  nav: { operations: 'العمليات', admin: 'الإدارة', reports: 'التقارير', system: 'النظام', dashboard: 'لوحة التحكم', transactions: 'المعاملات', newTransaction: 'معاملة جديدة', organizations: 'المؤسسات', auditLogs: 'سجل التدقيق', reportsTitle: 'التقارير', settings: 'الإعدادات' },
  actions: { save: 'حفظ', cancel: 'إلغاء', delete: 'حذف', edit: 'تعديل', create: 'إنشاء', search: 'بحث', clear: 'مسح', close: 'إغلاق', confirm: 'تأكيد', retry: 'إعادة المحاولة', back: 'العودة', viewAll: 'عرض الكل', logout: 'تسجيل خروج', loading: 'جاري التحميل...', noData: 'لا توجد بيانات', noResults: 'لا توجد نتائج تطابق معايير البحث', expand: 'توسيع القائمة', collapse: 'طي القائمة', confirmMessage: 'هل أنت متأكد؟' },
  status: { draft: 'مسودة', approved: 'معتمد', rejected: 'مرفوض', archived: 'مؤرشف', cancelled: 'ملغي', active: 'نشط', inactive: 'غير نشط' },
  roles: { admin: 'مدير', supervisor: 'مشرف', user: 'مستخدم', auditor: 'مدقق' },
  dashboard: { welcome: 'مرحباً', subtitle: 'لوحة التحكم — نظرة عامة على نظام الاستلام والتسليم المختبري', totalTransactions: 'إجمالي المعاملات', approved: 'معتمدة', draft: 'مسودة', organizations: 'المؤسسات', allTransactions: 'جميع المعاملات في النظام', approvedTransactions: 'المعاملات المعتمدة', pendingApproval: 'بانتظار الاعتماد', registeredOrgs: 'الجهات المسجلة', recentTransactions: 'آخر المعاملات', quickActions: 'إجراءات سريعة', newTransaction: 'معاملة جديدة', searchTransactions: 'بحث في المعاملات', manageOrgs: 'إدارة المؤسسات', reports: 'التقارير', monthly: 'شهري', dailyTrend: 'الاتجاه اليومي للمعاملات', lastSevenDays: 'عدد المعاملات المسجلة خلال آخر سبعة أيام', transactionsCount: 'معاملة', transactionTypes: 'توزيع أنواع المعاملات', mostUsedTypes: 'أكثر أنواع المعاملات استخدامًا', types: 'أنواع', statusDistribution: 'توزيع الحالات', noTrendData: 'لا توجد بيانات كافية لعرض الاتجاه', noTypeData: 'لا توجد بيانات لأنواع المعاملات', chartLabel: 'رسم بياني يوضح عدد المعاملات لكل يوم' },
  tx: { title: 'المعاملات', details: 'تفاصيل المعاملة', new: 'معاملة جديدة', searchPlaceholder: 'بحث برقم المعاملة أو اسم المرسل...', allStatus: 'جميع الحالات', from: 'من', to: 'إلى', total: 'إجمالي', transaction: 'معاملة', previous: 'السابق', next: 'التالي', notFound: 'المعاملة غير موجودة', noTransactions: 'لا توجد معاملات بعد', items: 'البنود', itemsCount: 'بند', approve: 'اعتماد', reject: 'رفض', archive: 'أرشفة', delete: 'حذف', deleteConfirm: 'هل أنت متأكد من حذف هذه المعاملة؟ لا يمكن التراجع عن هذا الإجراء.' },
  form: { transactionType: 'نوع المعاملة', transactionDate: 'تاريخ المعاملة', sender: 'المرسل', receiver: 'المستلم', senderOrg: 'المنشأة المرسلة', receiverOrg: 'المنشأة المستلمة', authorizationNo: 'رقم التفويض', authorizationDate: 'تاريخ التفويض', notes: 'ملاحظات', sampleType: 'نوع العينة', total: 'المجموع', valid: 'صالح', damaged: 'تالف', rejected: 'مرفوض', nonconforming: 'غير مطابق', transportCondition: 'حالة النقل', addItem: 'إضافة بند', removeItem: 'حذف', saveTransaction: 'حفظ المعاملة', senderJobTitle: 'مسمى المرسل', receiverJobTitle: 'مسمى المستلم', transportInfo: 'معلومات النقل', chooseType: 'اختر نوع المعاملة...', choose: 'اختر...', searchOrg: 'ابحث عن منشأة...', senderPlaceholder: 'اسم المرسل', receiverPlaceholder: 'اسم المستلم', extraNotes: 'ملاحظات إضافية...', chooseOrType: 'اختر أو اكتب...', good: 'جيدة', medium: 'متوسطة', poor: 'سيئة', createdSuccess: 'تم إنشاء المعاملة بنجاح', backToList: 'العودة إلى القائمة', saving: 'جاري الحفظ...', types: { receipt: 'استلام عينات', delivery: 'تسليم عينات', transfer: 'تحويل مختبري', return: 'إعادة عينات', results: 'تسليم نتائج', other: 'أخرى' } },
  org: { title: 'المؤسسات', add: 'إضافة مؤسسة', new: 'إضافة مؤسسة جديدة', name: 'اسم المؤسسة', code: 'الرمز', phone: 'الهاتف', email: 'البريد الإلكتروني', governorate: 'المحافظة', noOrgs: 'لا توجد مؤسسات', created: 'تم إنشاء المؤسسة بنجاح', nameLabel: 'الاسم', phoneLabel: 'الهاتف', emailLabel: 'البريد' },
  settings: { title: 'الإعدادات', noPermission: 'ليس لديك صلاحية الوصول إلى هذه الصفحة', userManagement: 'إدارة المستخدمين', addUser: 'إضافة مستخدم جديد', username: 'اسم المستخدم', fullName: 'الاسم الكامل', password: 'كلمة المرور', role: 'الصلاحية', status: 'الحالة', userCreated: 'تم إنشاء المستخدم بنجاح' },
  audit: { title: 'سجل التدقيق', noPermission: 'ليس لديك صلاحية الوصول إلى سجل التدقيق', noLogs: 'لا توجد سجلات', allActions: 'جميع الإجراءات', date: 'التاريخ', user: 'المستخدم', action: 'الإجراء', ip: 'IP', details: 'التفاصيل', changes: 'التغييرات', json: 'JSON', actions: { login_success: 'تسجيل دخول', login_failed: 'فشل تسجيل دخول', login_blocked: 'حظر تسجيل دخول', logout: 'تسجيل خروج', token_refreshed: 'تحديث رمز', password_changed: 'تغيير كلمة مرور', transaction_created: 'إنشاء معاملة', transaction_updated: 'تحديث معاملة', transaction_deleted: 'حذف معاملة', user_created: 'إنشاء مستخدم', user_updated: 'تحديث مستخدم', user_deleted: 'حذف مستخدم', org_created: 'إنشاء مؤسسة', org_updated: 'تحديث مؤسسة', org_deleted: 'حذف مؤسسة' } },
  reports: { title: 'التقارير', description: 'استعرض الإحصائيات وصدّر بيانات المعاملات حسب الفلاتر المطلوبة.', filters: 'فلاتر التقرير', startDate: 'من تاريخ', endDate: 'إلى تاريخ', allStatuses: 'كل الحالات', transactionTypePlaceholder: 'مثال: استلام', apply: 'تطبيق', reset: 'مسح', updating: 'جاري تحديث التقرير...', lastUpdated: 'آخر تحديث', summary: 'ملخص المعاملات', byType: 'حسب نوع المعاملة', total: 'إجمالي المعاملات', approved: 'معتمدة', draft: 'مسودة', rejected: 'مرفوضة', archived: 'مؤرشفة', cancelled: 'ملغاة', statusDistribution: 'توزيع الحالات', transactionData: 'بيانات المعاملات', matchingResults: 'نتيجة مطابقة للفلاتر الحالية', exportExcel: 'Excel', exportPdf: 'PDF', exporting: 'جاري التصدير...', noMatching: 'لا توجد معاملات مطابقة للفلاتر الحالية', noData: 'لا توجد بيانات', invalidDates: 'تاريخ البداية يجب أن يسبق تاريخ النهاية', loadFailed: 'تعذر تحميل التقرير', exportFailed: 'تعذر تصدير التقرير' },
  auth: { login: 'دخول', loginTitle: 'تسجيل الدخول إلى النظام', username: 'اسم المستخدم', password: 'كلمة المرور', usernamePlaceholder: 'أدخل اسم المستخدم', passwordPlaceholder: 'أدخل كلمة المرور', loggingIn: 'جاري تسجيل الدخول...', loginFailed: 'فشل تسجيل الدخول', changePassword: 'تغيير كلمة المرور' },
  notifications: { title: 'التنبيهات', open: 'فتح التنبيهات', unreadCount: 'عدد التنبيهات غير المقروءة', connected: 'متصل مباشرة', connecting: 'جاري الاتصال...', disconnected: 'غير متصل', markAllRead: 'تحديد الكل كمقروء', empty: 'لا توجد تنبيهات جديدة', parseError: 'تعذر قراءة تنبيه وارد', connectionError: 'تعذر الاتصال بالتنبيهات الفورية' },
  errors: { generic: 'حدث خطأ', loadFailed: 'فشل في تحميل البيانات', loadFailedTx: 'فشل في تحميل المعاملات', loadFailedTxDetail: 'فشل في تحميل المعاملة', loadFailedOrgs: 'فشل في تحميل المؤسسات', loadFailedAudit: 'فشل في تحميل سجل التدقيق', saveFailed: 'فشل في الحفظ', deleteFailed: 'فشل في الحذف', updateFailed: 'فشل في التحديث', notSpecified: 'لم يتم تحديد معاملة' },
}

const EN = {
  language: 'Language', arabic: 'العربية', english: 'English', switchToEnglish: 'English', switchToArabic: 'العربية',
  appName: 'Lab Receiving', appSubtitle: 'Laboratory Receiving and Delivery System', appFullName: 'Laboratory Receiving Management System',
  nav: { operations: 'Operations', admin: 'Administration', reports: 'Reports', system: 'System', dashboard: 'Dashboard', transactions: 'Transactions', newTransaction: 'New Transaction', organizations: 'Organizations', auditLogs: 'Audit Log', reportsTitle: 'Reports', settings: 'Settings' },
  actions: { save: 'Save', cancel: 'Cancel', delete: 'Delete', edit: 'Edit', create: 'Create', search: 'Search', clear: 'Clear', close: 'Close', confirm: 'Confirm', retry: 'Retry', back: 'Back', viewAll: 'View all', logout: 'Log out', loading: 'Loading...', noData: 'No data available', noResults: 'No results match your criteria', expand: 'Expand sidebar', collapse: 'Collapse sidebar', confirmMessage: 'Are you sure?' },
  status: { draft: 'Draft', approved: 'Approved', rejected: 'Rejected', archived: 'Archived', cancelled: 'Cancelled', active: 'Active', inactive: 'Inactive' },
  roles: { admin: 'Administrator', supervisor: 'Supervisor', user: 'User', auditor: 'Auditor' },
  dashboard: { welcome: 'Welcome', subtitle: 'Dashboard — overview of the laboratory receiving and delivery system', totalTransactions: 'Total transactions', approved: 'Approved', draft: 'Draft', organizations: 'Organizations', allTransactions: 'All transactions in the system', approvedTransactions: 'Approved transactions', pendingApproval: 'Pending approval', registeredOrgs: 'Registered organizations', recentTransactions: 'Recent transactions', quickActions: 'Quick actions', newTransaction: 'New transaction', searchTransactions: 'Search transactions', manageOrgs: 'Manage organizations', reports: 'Reports', monthly: 'Monthly', dailyTrend: 'Daily transaction trend', lastSevenDays: 'Transactions recorded over the last seven days', transactionsCount: 'transactions', transactionTypes: 'Transaction types', mostUsedTypes: 'Most frequently used types', types: 'types', statusDistribution: 'Status distribution', noTrendData: 'Not enough data to show the trend', noTypeData: 'No transaction type data', chartLabel: 'Chart showing the number of transactions per day' },
  tx: { title: 'Transactions', details: 'Transaction details', new: 'New transaction', searchPlaceholder: 'Search by transaction number or sender name...', allStatus: 'All statuses', from: 'From', to: 'To', total: 'Total', transaction: 'Transaction', previous: 'Previous', next: 'Next', notFound: 'Transaction not found', noTransactions: 'No transactions yet', items: 'Items', itemsCount: 'items', approve: 'Approve', reject: 'Reject', archive: 'Archive', delete: 'Delete', deleteConfirm: 'Are you sure you want to delete this transaction? This action cannot be undone.' },
  form: { transactionType: 'Transaction type', transactionDate: 'Transaction date', sender: 'Sender', receiver: 'Receiver', senderOrg: 'Sending organization', receiverOrg: 'Receiving organization', authorizationNo: 'Authorization number', authorizationDate: 'Authorization date', notes: 'Notes', sampleType: 'Sample type', total: 'Total', valid: 'Valid', damaged: 'Damaged', rejected: 'Rejected', nonconforming: 'Non-conforming', transportCondition: 'Transport condition', addItem: 'Add item', removeItem: 'Remove', saveTransaction: 'Save transaction', senderJobTitle: 'Sender job title', receiverJobTitle: 'Receiver job title', transportInfo: 'Transport information', chooseType: 'Select transaction type...', choose: 'Select...', searchOrg: 'Search for an organization...', senderPlaceholder: 'Sender name', receiverPlaceholder: 'Receiver name', extraNotes: 'Additional notes...', chooseOrType: 'Select or type...', good: 'Good', medium: 'Moderate', poor: 'Poor', createdSuccess: 'Transaction created successfully', backToList: 'Back to list', saving: 'Saving...', types: { receipt: 'Sample receipt', delivery: 'Sample delivery', transfer: 'Laboratory transfer', return: 'Sample return', results: 'Results delivery', other: 'Other' } },
  org: { title: 'Organizations', add: 'Add organization', new: 'New organization', name: 'Organization name', code: 'Code', phone: 'Phone', email: 'Email', governorate: 'Governorate', noOrgs: 'No organizations', created: 'Organization created successfully', nameLabel: 'Name', phoneLabel: 'Phone', emailLabel: 'Email' },
  settings: { title: 'Settings', noPermission: 'You do not have permission to access this page', userManagement: 'User management', addUser: 'Add new user', username: 'Username', fullName: 'Full name', password: 'Password', role: 'Role', status: 'Status', userCreated: 'User created successfully' },
  audit: { title: 'Audit log', noPermission: 'You do not have permission to access the audit log', noLogs: 'No logs', allActions: 'All actions', date: 'Date', user: 'User', action: 'Action', ip: 'IP', details: 'Details', changes: 'Changes', json: 'JSON', actions: { login_success: 'Sign in', login_failed: 'Sign in failed', login_blocked: 'Sign in blocked', logout: 'Sign out', token_refreshed: 'Token refreshed', password_changed: 'Password changed', transaction_created: 'Transaction created', transaction_updated: 'Transaction updated', transaction_deleted: 'Transaction deleted', user_created: 'User created', user_updated: 'User updated', user_deleted: 'User deleted', org_created: 'Organization created', org_updated: 'Organization updated', org_deleted: 'Organization deleted' } },
  reports: { title: 'Reports', description: 'Review statistics and export transaction data using the selected filters.', filters: 'Report filters', startDate: 'Start date', endDate: 'End date', allStatuses: 'All statuses', transactionTypePlaceholder: 'Example: Receipt', apply: 'Apply', reset: 'Clear', updating: 'Updating report...', lastUpdated: 'Last updated', summary: 'Transaction summary', byType: 'By transaction type', total: 'Total transactions', approved: 'Approved', draft: 'Draft', rejected: 'Rejected', archived: 'Archived', cancelled: 'Cancelled', statusDistribution: 'Status distribution', transactionData: 'Transaction data', matchingResults: 'matching results', exportExcel: 'Excel', exportPdf: 'PDF', exporting: 'Exporting...', noMatching: 'No transactions match the current filters', noData: 'No data available', invalidDates: 'Start date must be before end date', loadFailed: 'Unable to load the report', exportFailed: 'Unable to export the report' },
  auth: { login: 'Login', loginTitle: 'Sign in to the system', username: 'Username', password: 'Password', usernamePlaceholder: 'Enter username', passwordPlaceholder: 'Enter password', loggingIn: 'Signing in...', loginFailed: 'Sign in failed', changePassword: 'Change password' },
  notifications: { title: 'Notifications', open: 'Open notifications', unreadCount: 'Unread notification count', connected: 'Live connection', connecting: 'Connecting...', disconnected: 'Disconnected', markAllRead: 'Mark all as read', empty: 'No new notifications', parseError: 'Unable to read an incoming notification', connectionError: 'Unable to connect to live notifications' },
  errors: { generic: 'An error occurred', loadFailed: 'Failed to load data', loadFailedTx: 'Failed to load transactions', loadFailedTxDetail: 'Failed to load transaction', loadFailedOrgs: 'Failed to load organizations', loadFailedAudit: 'Failed to load audit log', saveFailed: 'Save failed', deleteFailed: 'Delete failed', updateFailed: 'Update failed', notSpecified: 'No transaction selected' },
}

const dictionaries = { ar: AR, en: EN }
const locale = ref(typeof window !== 'undefined' && localStorage.getItem('locale') === 'en' ? 'en' : 'ar')

function resolve(dictionary, path) {
  return path.split('.').reduce((value, key) => value?.[key], dictionary)
}

function translate(path) {
  return resolve(dictionaries[locale.value], path) ?? resolve(AR, path) ?? path
}

function createLocaleProxy(path = '') {
  return new Proxy({}, {
    get(_target, key) {
      if (typeof key === 'symbol') return undefined
      const nextPath = path ? `${path}.${key}` : key
      const value = translate(nextPath)
      return value && typeof value === 'object' ? createLocaleProxy(nextPath) : value
    },
  })
}

export const L = createLocaleProxy()
export const currentLocale = locale
export const t = translate

export function setLocale(nextLocale) {
  locale.value = nextLocale === 'en' ? 'en' : 'ar'
  if (typeof window !== 'undefined') localStorage.setItem('locale', locale.value)
}

export function toggleLocale() {
  setLocale(locale.value === 'ar' ? 'en' : 'ar')
}

export function useLocale() {
  const isArabic = computed(() => locale.value === 'ar')
  const direction = computed(() => (isArabic.value ? 'rtl' : 'ltr'))
  return { locale, isArabic, direction, t, setLocale, toggleLocale }
}

function applyDocumentLocale(value) {
  if (typeof document === 'undefined') return
  document.documentElement.lang = value
  document.documentElement.dir = value === 'ar' ? 'rtl' : 'ltr'
  document.body?.setAttribute('dir', value === 'ar' ? 'rtl' : 'ltr')
}

watch(locale, applyDocumentLocale, { immediate: true })
