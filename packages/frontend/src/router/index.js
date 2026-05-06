/**
 * 路由权限守卫
 * =============================================================
 *
 * 整个权限控制的入口。
 * 面试必问题：Vue Router 的导航守卫有哪些？执行顺序？
 *
 * Vue Router 导航守卫生命周期：
 *   1. 导航被触发
 *   2. beforeEach (全局前置守卫) ← 我们在这里做权限控制
 *   3. 组件内的 beforeRouteEnter
 *   4. 解析异步路由组件
 *   5. 确认导航
 *   6. afterEach (全局后置守卫)
 *
 * 为什么在 beforeEach 而不是其他守卫？
 *   —— beforeEach 在路由确定之前执行
 *   —— 适合拦截未登录/无权限的用户
 *   —— 可以在此处加载菜单、生成路由
 *
 * 权限控制流程：
 *   用户访问 /dashboard
 *     → beforeEach 检查是否登录
 *       → 未登录 → 跳转 /login
 *       → 已登录 → 检查是否已加载菜单
 *         → 未加载 → 加载菜单树 → 动态注册路由
 *         → 已加载 → 确认导航
 */

import router from './index'
import store from '@/store'
import { Message } from '@arco-design/web-vue'

// 菜单是否已加载（防止重复加载）
let menuLoaded = false

router.beforeEach(async (to, from, next) => {
  // ════════════════════════════════════════════════
  // 规则1：公开页面直接放行
  // ════════════════════════════════════════════════
  const publicPaths = ['/login', '/404', '/shop']
  if (publicPaths.some(p => to.path.startsWith(p))) {
    if (to.path === '/login') {
      menuLoaded = false  // 退出时重置
    }
    next()
    return
  }

  // ════════════════════════════════════════════════
  // 规则2：未登录 → 跳转登录页
  // ════════════════════════════════════════════════
  // 从 Vuex state 读取用户信息（页面刷新后 state 清空，需要重新获取）
  if (!store.state.user.id) {
    try {
      const ok = await store.dispatch('user/getUserInfo')
      if (!ok) {
        Message.info('请先登录')
        next('/login')
        return
      }
    } catch (e) {
      Message.info('请先登录')
      next('/login')
      return
    }
  }

  // ════════════════════════════════════════════════
  // 规则3：首次访问，加载菜单树并注册动态路由
  // ════════════════════════════════════════════════
  if (!menuLoaded) {
    const ok = await store.dispatch('menu/getMenuTree')
    if (ok) {
      const menuTree = store.state.menu.menuTree
      if (menuTree && menuTree.length > 0) {
        // 动态路由注册
        addDynamicRoutes(menuTree)
        menuLoaded = true

        // 根路径 → 重定向到第一个菜单
        if (to.path === '/' || to.matched.length === 0) {
          const firstPath = findFirstMenuPath(menuTree)
          if (firstPath) { next(firstPath); return }
        }
      }
    }
  }

  // ════════════════════════════════════════════════
  // 规则4：404 fallback
  // ════════════════════════════════════════════════
  if (to.matched.length === 0) {
    const menuTree = store.state.menu.menuTree
    if (menuTree?.length > 0) {
      const firstPath = findFirstMenuPath(menuTree)
      if (firstPath) { next(firstPath); return }
    }
  }

  // 放行
  next()
})

/**
 * 动态路由注册
 *
 * 菜单树 → 前端路由的转换逻辑：
 *   后端 Menu { path, component, children } → 前端 RouteRecordRaw
 *
 * 为什么要动态注册？
 *   —— 不同用户有不同菜单（权限不同，菜单不同）
 *   —— 路由不写死，由后端菜单数据决定
 */
function addDynamicRoutes(menuTree) {
  const routes = menuTreeToRoutes(menuTree)

  routes.forEach(route => {
    try {
      router.addRoute(route)
    } catch (e) {
      console.error('[router] addRoute failed:', route, e)
    }
  })

  // 添加 catchAll 路由（未匹配路径 → 404）
  if (!router.hasRoute('catchAll')) {
    router.addRoute({
      name: 'catchAll',
      path: '/:catchAll(.*)',
      redirect: '/404',
      hidden: true,
    })
  }
}

/**
 * 菜单树 → 路由数组
 *
 * 核心转换逻辑（面试重点）：
 *   parentPath + childPath = 完整路径
 *
 * 示例：
 *   后端: [{ title: '系统', path: '/system', children: [{ title: '用户', path: '/user' }] }]
 *   前端: [{ path: '/system', children: [{ path: '/system/user' }] }]
 */
function menuTreeToRoutes(tree, parentPath = '') {
  const routes = []

  for (const menu of tree) {
    // 跳过隐藏菜单
    if (menu.isHidden) continue

    // 路径处理：parentPath/childPath
    const fullPath = joinPath(parentPath, menu.path)
    const hasChildren = menu.children && menu.children.length > 0

    const route = {
      name: menu.name || `menu_${menu.id}`,
      path: fullPath,
      // 布局组件（叶子节点或有子菜单都用 Layout）
      component: loadLayoutComponent(),
      hidden: !!menu.isHidden,
      meta: {
        title: menu.title,
        icon: menu.icon,
        id: menu.id,
      },
    }

    // 有子菜单 → 递归，嵌套路由
    if (hasChildren) {
      route.children = menuTreeToRoutes(menu.children, fullPath)
    } else if (menu.component) {
      // 叶子节点 → 直接注册组件
      route.children = [{
        path: '',
        name: route.name,
        component: loadViewComponent(menu.component),
        meta: route.meta,
      }]
    }

    routes.push(route)
  }

  return routes
}

// 布局组件懒加载
function loadLayoutComponent() {
  return () => import('@/layout/content/index.vue')
}

// 视图组件懒加载
function loadViewComponent(componentPath) {
  return () => import(`@/views/${componentPath}.vue`)
}

// 路径拼接（去除多余斜杠）
function joinPath(parent, child) {
  const normalize = (p) => (p || '').replace(/^\/+|\/+$/g, '')
  const a = normalize(parent)
  const b = normalize(child)
  if (!a && !b) return '/'
  if (!a) return `/${b}`
  if (!b) return `/${a}`
  return `/${a}/${b}`
}

/**
 * 查找第一个叶子菜单的路径（用于根路径重定向）
 */
function findFirstMenuPath(tree, parentPath = '') {
  for (const menu of tree) {
    const fullPath = joinPath(parentPath, menu.path)
    if (menu.children?.length > 0) {
      const found = findFirstMenuPath(menu.children, fullPath)
      if (found) return found
    } else if (menu.path) {
      return fullPath || '/'
    }
  }
  return null
}

export { addDynamicRoutes, menuTreeToRoutes }
export default router
