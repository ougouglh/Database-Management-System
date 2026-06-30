import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/home',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '功能导航' }
      },
      {
        path: 'data',
        name: 'DataView',
        component: () => import('@/views/DataView.vue'),
        meta: { title: '汇总表查看' }
      },
      {
        path: 'import',
        name: 'Import',
        component: () => import('@/views/ImportPage.vue'),
        meta: { title: '数据导入' }
      },
      {
        path: 'export',
        name: 'Export',
        component: () => import('@/views/ExportPage.vue'),
        meta: { title: '数据导出' }
      },
      {
        path: 'filter',
        name: 'FilterExport',
        component: () => import('@/views/FilterExport.vue'),
        meta: { title: '筛选导出' }
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/LogPage.vue'),
        meta: { title: '操作日志' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth !== false && !userStore.isLoggedIn()) {
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn()) {
    next('/home')
  } else {
    next()
  }
})

export default router
