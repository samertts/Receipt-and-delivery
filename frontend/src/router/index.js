import { createRouter, createWebHistory } from 'vue-router'
const pages = ['Login','Dashboard','NewTransaction','TransactionsList','TransactionDetails','Reports','Organizations','Settings','AuditLogs']
const routes = pages.map(n => ({ path: n==='Login' ? '/' : `/${n.toLowerCase()}`, component: () => import(`../pages/${n}.vue`) }))
export default createRouter({ history: createWebHistory(), routes })
