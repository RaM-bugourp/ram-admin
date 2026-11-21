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
            { path: 'system/audit', name: 'CoreAudit', component: () => import('@/views/system/AuditView.vue'), meta: { title: '操作审计', permission: 'audit.read' } },
            { path: 'settings', name: 'Settings', component: () => import('@/views/system/SettingsView.vue'), meta: { title: '个人设置' } },
            { path: '', redirect: '/dashboard' },
            {
                path: 'dashboard',
                name: 'Dashboard',
                component: () => import('@/views/dashboard/DashboardView.vue'),
                meta: { title: '仪表盘' },
            },
            {
                path: 'system/users',
                name: 'UserList',
                component: () => import('@/views/system/user/UserListView.vue'),
                meta: { title: '用户管理' },
            },
            {
                path: 'system/roles',
                name: 'RoleList',
                component: () => import('@/views/system/role/RoleListView.vue'),
                meta: { title: '角色管理' },
            },
            // ── AI 模块（仅 root）───────────────────────────
            {
                path: 'ai/chat',
                name: 'AIChat',
                component: () => import('@/views/ai/AIChatView.vue'),
                meta: { title: 'AI 对话', requireRoot: true },
            },
            {
                path: 'ai/approval',
                name: 'AIApproval',
                component: () => import('@/views/ai/AIApprovalView.vue'),
                meta: { title: 'Agent 审批', requireRoot: true },
            },
            {
                path: 'ai/audit',
                name: 'AIAudit',
                component: () => import('@/views/ai/AIAuditView.vue'),
                meta: { title: 'AI 审计', requireRoot: true },
            },
            {
                path: 'ai/notifications',
                name: 'AINotification',
                component: () => import('@/views/ai/AINotificationView.vue'),
                meta: { title: 'AI 通知', requireRoot: true },
            },
            {
                path: 'ai/agent-token',
                name: 'AIAgentToken',
                component: () => import('@/views/ai/AIAgentTokenView.vue'),
                meta: { title: 'Agent Token', requireRoot: true },
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

router.beforeEach(async (to, _from, next) => {
    await store.dispatch('user/bootstrap')
    if (to.meta.requiresAuth !== false && !store.getters['user/isAuthenticated']) return next('/login')
    const required = to.path === '/system/users' ? 'users.read' : to.path === '/system/roles' ? 'roles.read' : to.meta.permission
    if (required && !store.getters['user/can'](required)) return next('/403')
    if (to.path.startsWith('/ai/') && !store.state.user.aiEnabled) return next('/403')
    if (to.meta.requiresAuth !== false && !store.getters['user/isAuthenticated']) {
        return next('/login')
    }
    // root 专属路由（AI 模块）
    if (to.meta.requireRoot && !store.getters['user/isRoot']) {
        return next('/403')
    }
    next()
})

export default router
