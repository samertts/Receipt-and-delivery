export const STATUS_LABELS = {
  draft: 'مسودة',
  approved: 'معتمد',
  rejected: 'مرفوض',
  archived: 'مؤرشف',
  cancelled: 'ملغي',
}

export const STATUS_CLASSES = {
  draft: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200',
  approved: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200',
  rejected: 'bg-red-50 text-red-700 ring-1 ring-red-200',
  archived: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
  cancelled: 'bg-slate-100 text-slate-600 ring-1 ring-slate-200',
}

export const ROLE_LABELS = {
  admin: 'مدير',
  supervisor: 'مشرف',
  user: 'مستخدم',
  auditor: 'مدقق',
}

export function statusLabel(status) {
  return STATUS_LABELS[status] || status
}

export function statusClass(status) {
  return STATUS_CLASSES[status] || 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
}

export function roleLabel(role) {
  return ROLE_LABELS[role] || role
}

export function formatDate(dateStr) {
  if (!dateStr) return '-'
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('ar-IQ', { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}
