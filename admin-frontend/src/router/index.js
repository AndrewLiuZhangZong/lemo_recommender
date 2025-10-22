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
      },
      {
        path: '/jobs',
        name: 'Jobs',
        component: () => import('../views/Jobs.vue'),
        meta: { title: '作业管理' }
      },
      {
        path: '/model-training',
        name: 'ModelTraining',
        component: () => import('../views/ModelTraining.vue'),
        meta: { title: '模型训练' }
      },
      {
        path: '/recall-config',
        name: 'RecallConfig',
        component: () => import('../views/RecallConfig.vue'),
        meta: { title: '召回配置' }
      },
      {
        path: '/model-management',
        name: 'ModelManagement',
        component: () => import('../views/ModelManagement.vue'),
        meta: { title: '模型管理' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

