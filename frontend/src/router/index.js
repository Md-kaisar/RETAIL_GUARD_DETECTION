import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/store/auth'

const routes = [
  { path: '/login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', component: () => import('@/views/DashboardView.vue') },
      { path: 'transactions', component: () => import('@/views/TransactionsView.vue') },
      { path: 'transactions/upload', component: () => import('@/views/UploadView.vue') },
      { path: 'alerts', component: () => import('@/views/AlertsView.vue') },
      { path: 'cases', component: () => import('@/views/CasesView.vue') },
      { path: 'cases/:id', component: () => import('@/views/CaseDetailView.vue') },
      { path: 'users', component: () => import('@/views/UsersView.vue') },
      { path: 'audit', component: () => import('@/views/AuditView.vue') },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) return '/login'
  if (to.path === '/login' && auth.isLoggedIn) return '/dashboard'
})

export default router
