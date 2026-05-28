import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'Login', component: () => import('../pages/Login.vue'), meta: { guest: true } },
  { path: '/dashboard', name: 'Dashboard', component: () => import('../pages/Dashboard.vue'), meta: { requiresAuth: true } },
  { path: '/newtransaction', name: 'NewTransaction', component: () => import('../pages/NewTransaction.vue'), meta: { requiresAuth: true } },
  { path: '/transactionslist', name: 'TransactionsList', component: () => import('../pages/TransactionsList.vue'), meta: { requiresAuth: true } },
  { path: '/transactiondetails', name: 'TransactionDetails', component: () => import('../pages/TransactionDetails.vue'), meta: { requiresAuth: true } },
  { path: '/reports', name: 'Reports', component: () => import('../pages/Reports.vue'), meta: { requiresAuth: true } },
  { path: '/organizations', name: 'Organizations', component: () => import('../pages/Organizations.vue'), meta: { requiresAuth: true } },
  { path: '/settings', name: 'Settings', component: () => import('../pages/Settings.vue'), meta: { requiresAuth: true } },
  { path: '/auditlogs', name: 'AuditLogs', component: () => import('../pages/AuditLogs.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/')
  } else if (to.meta.guest && auth.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
