export const L = {
  appName: 'الاستلام المختبري',
  appSubtitle: 'نظام الاستلام والتسليم المختبري',
  appFullName: 'نظام إدارة الاستلام المختبري',

  // Navigation
  nav: {
    operations: 'العمليات',
    admin: 'الإدارة',
    reports: 'التقارير',
    system: 'النظام',
    dashboard: 'لوحة التحكم',
    transactions: 'المعاملات',
    newTransaction: 'معاملة جديدة',
    organizations: 'المؤسسات',
    auditLogs: 'سجل التدقيق',
    reportsTitle: 'التقارير',
    settings: 'الإعدادات',
  },

  // Common actions
  actions: {
    save: 'حفظ',
    cancel: 'إلغاء',
    delete: 'حذف',
    edit: 'تعديل',
    create: 'إنشاء',
    search: 'بحث',
    clear: 'مسح',
    close: 'إغلاق',
    confirm: 'تأكيد',
    retry: 'إعادة المحاولة',
    back: 'العودة',
    viewAll: 'عرض الكل',
    logout: 'تسجيل خروج',
    loading: 'جاري التحميل...',
    noData: 'لا توجد بيانات',
    noResults: 'لا توجد نتائج تطابق معايير البحث',
  },

  // Status
  status: {
    draft: 'مسودة',
    approved: 'معتمد',
    rejected: 'مرفوض',
    archived: 'مؤرشف',
    cancelled: 'ملغي',
    active: 'نشط',
    inactive: 'غير نشط',
  },

  // Roles
  roles: {
    admin: 'مدير',
    supervisor: 'مشرف',
    user: 'مستخدم',
    auditor: 'مدقق',
  },

  // Dashboard
  dashboard: {
    welcome: 'مرحباً',
    subtitle: 'لوحة التحكم — نظرة عامة على نظام الاستلام والتسليم المختبري',
    totalTransactions: 'إجمالي المعاملات',
    approved: 'معتمدة',
    draft: 'مسودة',
    organizations: 'المؤسسات',
    allTransactions: 'جميع المعاملات في النظام',
    approvedTransactions: 'المعاملات المعتمدة',
    pendingApproval: 'بانتظار الاعتماد',
    registeredOrgs: 'الجهات المسجلة',
    recentTransactions: 'آخر المعاملات',
    quickActions: 'إجراءات سريعة',
    newTransaction: 'معاملة جديدة',
    searchTransactions: 'بحث في المعاملات',
    manageOrgs: 'إدارة المؤسسات',
    reports: 'التقارير',
  },

  // Transactions
  tx: {
    title: 'المعاملات',
    details: 'تفاصيل المعاملة',
    new: 'معاملة جديدة',
    searchPlaceholder: 'بحث برقم المعاملة أو اسم المرسل...',
    allStatus: 'جميع الحالات',
    from: 'من',
    to: 'إلى',
    total: 'إجمالي',
    transaction: 'معاملة',
    previous: 'السابق',
    next: 'التالي',
    notFound: 'المعاملة غير موجودة',
    noTransactions: 'لا توجد معاملات بعد',
    items: 'البنود',
    itemsCount: 'بند',
    approve: 'اعتماد',
    reject: 'رفض',
    archive: 'أرشفة',
    delete: 'حذف',
    deleteConfirm: 'هل أنت متأكد من حذف هذه المعاملة؟ لا يمكن التراجع عن هذا الإجراء.',
  },

  // Form labels
  form: {
    transactionType: 'نوع المعاملة',
    transactionDate: 'تاريخ المعاملة',
    sender: 'المرسل',
    receiver: 'المستلم',
    senderOrg: 'المنشأة المرسلة',
    receiverOrg: 'المنشأة المستلمة',
    authorizationNo: 'رقم التفويض',
    authorizationDate: 'تاريخ التفويض',
    notes: 'ملاحظات',
    sampleType: 'نوع العينة',
    total: 'المجموع',
    valid: 'صالح',
    damaged: 'تالف',
    rejected: 'مرفوض',
    nonconforming: 'غير مطابق',
    transportCondition: 'حالة النقل',
    addItem: 'إضافة بند',
    removeItem: 'حذف',
    saveTransaction: 'حفظ المعاملة',
    senderJobTitle: 'مسمى المرسل',
    receiverJobTitle: 'مسمى المستلم',
    transportInfo: 'معلومات النقل',
  },

  // Organizations
  org: {
    title: 'المؤسسات',
    add: 'إضافة مؤسسة',
    new: 'إضافة مؤسسة جديدة',
    name: 'اسم المؤسسة',
    code: 'الرمز',
    phone: 'الهاتف',
    email: 'البريد الإلكتروني',
    governorate: 'المحافظة',
    noOrgs: 'لا توجد مؤسسات',
    created: 'تم إنشاء المؤسسة بنجاح',
    nameLabel: 'الاسم',
    phoneLabel: 'الهاتف',
    emailLabel: 'البريد',
  },

  // Settings
  settings: {
    title: 'الإعدادات',
    noPermission: 'ليس لديك صلاحية الوصول إلى هذه الصفحة',
    userManagement: 'إدارة المستخدمين',
    addUser: 'إضافة مستخدم جديد',
    username: 'اسم المستخدم',
    fullName: 'الاسم الكامل',
    password: 'كلمة المرور',
    role: 'الصلاحية',
    status: 'الحالة',
    userCreated: 'تم إنشاء المستخدم بنجاح',
  },

  // Audit
  audit: {
    title: 'سجل التدقيق',
    noPermission: 'ليس لديك صلاحية الوصول إلى سجل التدقيق',
    noLogs: 'لا توجد سجلات',
    allActions: 'جميع الإجراءات',
    date: 'التاريخ',
    user: 'المستخدم',
    action: 'الإجراء',
    ip: 'IP',
    details: 'التفاصيل',
    changes: 'التغييرات',
  },

  // Reports
  reports: {
    title: 'التقارير',
    summary: 'ملخص المعاملات',
    byType: 'حسب نوع المعاملة',
    total: 'إجمالي المعاملات',
    approved: 'معتمدة',
    draft: 'مسودة',
    rejected: 'مرفوضة',
    noData: 'لا توجد بيانات',
  },

  // Auth
  auth: {
    login: 'دخول',
    loginTitle: 'تسجيل الدخول إلى النظام',
    username: 'اسم المستخدم',
    password: 'كلمة المرور',
    usernamePlaceholder: 'أدخل اسم المستخدم',
    passwordPlaceholder: 'أدخل كلمة المرور',
    loggingIn: 'جاري تسجيل الدخول...',
    loginFailed: 'فشل تسجيل الدخول',
    changePassword: 'تغيير كلمة المرور',
  },

  // Errors
  errors: {
    generic: 'حدث خطأ',
    loadFailed: 'فشل في تحميل البيانات',
    loadFailedTx: 'فشل في تحميل المعاملات',
    loadFailedTxDetail: 'فشل في تحميل المعاملة',
    loadFailedOrgs: 'فشل في تحميل المؤسسات',
    loadFailedAudit: 'فشل في تحميل سجل التدقيق',
    saveFailed: 'فشل في الحفظ',
    deleteFailed: 'فشل في الحذف',
    updateFailed: 'فشل في التحديث',
    notSpecified: 'لم يتم تحديد معاملة',
  },
}

export function t(path) {
  return path.split('.').reduce((acc, key) => acc?.[key], L) || path
}
