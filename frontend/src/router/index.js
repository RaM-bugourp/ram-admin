/**
 * 前端路由配置
 * =============================================================
 *
 * 路由分两类：
 *   1. 静态路由 —— 不需要后端菜单授权，所有人都能访问
 *   2. 动态路由 —— 从后端菜单树生成，用户授权后才能访问
 *
 * 路由守卫 beforeEach 在这里处理权限控制。
 */

import { createRouter, createWebHistory } from 'vue-router'

// ─────────────────────────────────────────────────────────────────
// 1. 静态路由（始终可用）
// ─────────────────────────────────────────────────────────────────

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/index.vue'),
    meta: { title: '登录', hidden: true },
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/404.vue'),
    meta: { title: '404', hidden: true },
  },
]

// ─────────────────────────────────────────────────────────────────
// 2. 创建路由实例
// ─────────────────────────────────────────────────────────────────

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// ─────────────────────────────────────────────────────────────────
// 3. 全局前置守卫（权限控制核心）
// ─────────────────────────────────────────────────────────────────

let menuLoaded = false

router.beforeEach(async (to, from, next) => {
  // 页面标题
  document.title = (to.meta.title || 'RaM Admin') + ' - RaM Admin'

  // 公开页面直接放行
  if (to.path === '/login' || to.path === '/404') {
    menuLoaded = false
    next()
    return
  }

  // 未登录 → 跳转登录页
  if (!window.__userId__) {
    // 页面刷新后状态丢失，从后端重新获取用户信息
    const storedUser = localStorage.getItem('user')
    if (!storedUser) {
      next('/login')
      return
    }
    try {
      const ok = await _fetchUserInfo()
      if (!ok) { next('/login'); return }
    } catch {
      next('/login')
      return
    }
  }

  // 首次访问，加载菜单树并注册动态路由
  if (!menuLoaded) {
    await _loadMenuAndRoutes()
    menuLoaded = true
    // addRoute 后当前导航的 matched 可能还是空的，需要重新触发
    next({ ...to, replace: true })
    return
  }

  next()
})

// ─────────────────────────────────────────────────────────────────
// 4. 辅助函数
// ─────────────────────────────────────────────────────────────────

async function _fetchUserInfo() {
  try {
    const res = await fetch('/api/auth/user_info/', {
      credentials: 'include',
    })
    if (!res.ok) return false
    const data = await res.json()
    window.__userId__ = data.id
    window.__userInfo__ = data
    return true
  } catch {
    return false
  }
}

async function _loadMenuAndRoutes() {
  try {
    const res = await fetch('/api/system/menu/tree/', {
      credentials: 'include',
    })
    if (!res.ok) return false
    const menuTree = await res.json()

    if (!Array.isArray(menuTree) || menuTree.length === 0) {
      // 没有菜单数据，只注册基本路由
      _addBasicRoutes()
      return true
    }

    // 动态路由注册
    const dynamicRoutes = _menuTreeToRoutes(menuTree)
    dynamicRoutes.forEach(route => {
      if (!router.hasRoute(route.name)) {
        router.addRoute(route)
      }
    })

    // 添加 catchAll
    if (!router.hasRoute('catchAll')) {
      router.addRoute({ path: '/:pathMatch(.*)*', redirect: '/404', name: 'catchAll' })
    }

    return true
  } catch {
    return false
  }
}

function _addBasicRoutes() {
  const basics = [
    { path: '/', redirect: '/dashboard', name: 'Home' },
    { path: '/dashboard', name: 'Dashboard', component: () => import('@/views/dashboard/index.vue'), meta: { title: '首页' } },
    { path: '/article/list', name: 'ArticleList', component: () => import('@/views/article/list.vue'), meta: { title: '文章列表' } },
  ]
  basics.forEach(r => {
    if (!router.hasRoute(r.name)) router.addRoute(r)
  })
  if (!router.hasRoute('catchAll')) {
    router.addRoute({ path: '/:pathMatch(.*)*', redirect: '/404', name: 'catchAll' })
  }
}

function _menuTreeToRoutes(tree, parentPath = '') {
  const routes = []

  for (const menu of tree) {
    if (menu.isHidden) continue

    const fullPath = _joinPath(parentPath, menu.path)
    const hasChildren = menu.children?.length > 0

    const route = {
      name: menu.name || `menu_${menu.id}`,
      path: fullPath,
      component: () => import('@/layout/content/index.vue'),
      meta: { title: menu.title, icon: menu.icon },
      children: [],
    }

    if (hasChildren) {
      route.children = _menuTreeToRoutes(menu.children, fullPath)
    } else if (menu.component) {
      route.children = [{
        path: '',
        name: route.name + '_index',
        component: () => import(`@/views/${menu.component}.vue`),
        meta: route.meta,
      }]
    }

    routes.push(route)
  }

  return routes
}

function _joinPath(parent, child) {
  const n = (p) => (p || '').replace(/^\/+|\/+$/g, '')
  const a = n(parent), b = n(child)
  if (!a && !b) return '/'
  if (!a) return `/${b}`
  if (!b) return `/${a}`
  return `/${a}/${b}`
}

export default router
