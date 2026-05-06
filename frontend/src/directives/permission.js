/**
 * 权限指令
 * =============================================================
 *
 * 用法：
 *   <a-button v-permission="'user:create'">创建用户</a-button>
 *   <a-button v-permission="['user:edit', 'user:admin']">编辑</a-button>
 *
 * 没有权限时元素会被移除（类似 v-if）
 */

import { useStore } from 'vuex'

export const permission = {
  mounted(el, binding) {
    const store = useStore()
    const value = binding.value

    // 超级用户直接放行
    if (store.state.user.is_superuser) return

    // 获取用户权限列表
    const permissions = store.state.user.permissions || []

    // 检查权限
    let hasPermission = false
    if (Array.isArray(value)) {
      // 数组：满足任一即可
      hasPermission = value.some((p) => permissions.includes(p))
    } else {
      // 字符串：精确匹配
      hasPermission = permissions.includes(value)
    }

    // 无权限则移除元素
    if (!hasPermission) {
      el.parentNode?.removeChild(el)
    }
  },
}

/**
 * 角色指令
 * =============================================================
 *
 * 用法：
 *   <div v-role="'admin'">仅管理员可见</div>
 *   <div v-role="['admin', 'editor']">管理员或编辑可见</div>
 */
export const role = {
  mounted(el, binding) {
    const store = useStore()
    const value = binding.value

    // 超级用户直接放行
    if (store.state.user.is_superuser) return

    // 获取用户角色列表
    const roles = store.state.user.roles || []

    // 检查角色
    let hasRole = false
    if (Array.isArray(value)) {
      hasRole = value.some((r) => roles.includes(r))
    } else {
      hasRole = roles.includes(value)
    }

    // 无角色则移除元素
    if (!hasRole) {
      el.parentNode?.removeChild(el)
    }
  },
}

/**
 * 注册所有指令
 */
export function setupDirectives(app) {
  app.directive('permission', permission)
  app.directive('role', role)
}
