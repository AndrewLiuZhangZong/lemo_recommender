import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表板' }
      },
      {
        path: '/scenarios',
        name: 'Scenarios',
        component: () => import('../views/Scenarios.vue'),
        meta: { title: '场景管理' }
      },
      {
        path: '/items',
        name: 'Items',
        component: () => import('../views/Items.vue'),
        meta: { title: '物品管理' }
      },
      {
        path: '/experiments',
        name: 'Experiments',
        component: () => import('../views/Experiments.vue'),
        meta: { title: 'AB实验' }
      },
      {
        path: '/analytics',
        name: 'Analytics',
        component: () => import('../views/Analytics.vue'),
        meta: { title: '数据分析' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

