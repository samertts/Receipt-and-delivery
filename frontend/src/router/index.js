import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'Login', component: () => import('../pages/Login.vue'), meta: { guest: true } },
  { path: '/forbidden', name: 'Forbidden', component: () => import('../pages/Forbidden.vue'), meta: { requiresAuth: true } },
  { path: '/devices', name: 'Devices', component: () => import('../pages/Devices.vue'), meta: { requiresAuth: true, permission: 'use_devices' } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true, permission: 'view_dashboard' } },
  { path: '/newtransaction', name: 'NewTransaction', component: () => import('../pages/NewTransaction.vue'), meta: { requiresAuth: true, permission: 'create_transaction' } },
  { path: '/transactionslist', name: 'TransactionsList', component: () => import('../pages/TransactionsList.vue'), meta: { requiresAuth: true, permission: 'view_transactions' } },
  { path: '/transactiondetails', name: 'TransactionDetails', component: () => import('../pages/TransactionDetails.vue'), meta: { requiresAuth: true, permission: 'view_transactions' } },
  { path: '/reports', name: 'Reports', component: () => import('../pages/Reports.vue'), meta: { requiresAuth: true, permission: 'view_reports' } },
  { path: '/organizations', name: 'Organizations', component: () => import('../pages/Organizations.vue'), meta: { requiresAuth: true, permission: 'view_organizations' } },
  { path: '/settings', name: 'Settings', component: () => import('../pages/Settings.vue'), meta: { requiresAuth: true, permission: 'manage_settings' } },
  { path: '/auditlogs', name: 'AuditLogs', component: () => import('../pages/AuditLogs.vue'), meta: { requiresAuth: true, permission: 'view_audit_logs' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/')
    return
  }
  if (to.meta.guest && auth.isAuthenticated) {
    next('/dashboard')
    return
  }
  if (auth.isAuthenticated && !auth.permissions.length) {
    try {
      await auth.loadProfile()
    } catch {
      // The API interceptor handles expired sessions; the guard denies unknown permissions.
    }
  }
  if (to.meta.permission && !auth.hasPermission(to.meta.permission)) {
    next({ name: 'Forbidden' })
    return
  }
  next()
})

export default router
