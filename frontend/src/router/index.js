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
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
