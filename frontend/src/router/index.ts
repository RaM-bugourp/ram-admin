import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import store from '@/stores'

const routes: RouteRecordRaw[] = [
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/login/LoginView.vue'),
        meta: { requiresAuth: false },
    },
    {
        path: '/',
        component: () => import('@/layouts/MainLayout.vue'),
        meta: { requiresAuth: true },
        children: [
            { path: '', redirect: '/dashboard' },
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/dashboard/DashboardView.vue'),
                meta: { title: '仪表盘' },
            },
        ],
    },
    {
        path: '/403',
        name: 'Forbidden',
        component: () => import('@/views/error/ForbiddenView.vue'),
        meta: { requiresAuth: false },
    },
    {
        path: '/:pathMatch(.*)*',
        name: 'NotFound',
        component: () => import('@/views/error/NotFoundView.vue'),
        meta: { requiresAuth: false },
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes,
})

router.beforeEach((to, _from, next) => {
    if (to.meta.requiresAuth !== false && !store.getters['user/isAuthenticated']) {
        return next('/login')
    }
    next()
})

export default router
