import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/servers',
    name: 'Servers',
    component: () => import('@/views/Servers.vue')
  },
  {
    path: '/servers/:id',
    name: 'ServerDetail',
    component: () => import('@/views/ServerDetail.vue')
  },
  {
    path: '/databases',
    name: 'Databases',
    component: () => import('@/views/Databases.vue')
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue')
  },
  {
    path: '/logs',
    name: 'Logs',
    component: () => import('@/views/Logs.vue')
  },
  {
    path: '/admin',
    name: 'Admin',
    component: () => import('@/views/Admin.vue')
  },
  // Oracle Database Operations Monitoring
  {
    path: '/oracle-ops',
    name: 'OracleOps',
    component: () => import('@/views/OracleOps.vue')
  },
  {
    path: '/oracle-ops/:id',
    name: 'OracleOpsDetail',
    component: () => import('@/views/OracleOpsDetail.vue')
  },
  {
    path: '/oracle-ops-backups',
    name: 'OracleOpsBackups',
    component: () => import('@/views/OracleOpsBackups.vue')
  },
  {
    path: '/oracle-ops-alerts',
    name: 'OracleOpsAlerts',
    component: () => import('@/views/OracleOpsAlerts.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
