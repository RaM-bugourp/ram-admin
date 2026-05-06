/**
 * 用户认证 Store
 * =============================================================
 *
 * 负责：登录、登出、获取用户信息、权限码管理
 *
 * 为什么用 Vuex？
 *   —— 跨组件共享用户状态（Navbar 需要显示用户名、侧边栏需要权限信息）
 *   —— 页面刷新后保持状态（配合 localStorage）
 *   —— 与路由守卫配合：登录状态决定能否访问某个页面
 *
 * Vuex vs Pinia：
 *   Vuex：Vue 3 官方推荐，更成熟，模块化清晰
 *   Pinia：更轻量，API 更现代，Composition API 友好
 *   本框架保持 Vuex（兼容 Vue 2），但设计思想两种都适用
 */

import { login as apiLogin, logout as apiLogout, getUserInfo as apiGetUserInfo } from '@/api/user'

const getDefaultState = () => ({
  id: null,
  username: '',
  email: '',
  is_superuser: false,
  // roles: [{ code: 'admin', name: '管理员' }]
  roles: [],
  // permissions: ['article:list', 'article:create']
  permissions: [],
  primary_organization: null,
})

export default {
  namespaced: true,

  state: getDefaultState(),

  getters: {
    /**
     * 检查是否拥有指定权限码
     *
     * 用法：
     *   this.$store.getters['user/hasPermission']('article:list')
     *   或者辅助函数：const hasPermission = usePermission() // Pinia 用法
     */
    hasPermission: (state) => (code) => {
      if (state.is_superuser) return true
      return state.permissions.includes(code)
    },

    /**
     * 检查是否拥有指定角色
     */
    hasRole: (state) => (code) => {
      if (state.is_superuser) return true
      return state.roles.some(r => r.code === code)
    },

    /**
     * 是否已登录
     */
    isLoggedIn: (state) => !!state.id,
  },

  mutations: {
    SET_USER_INFO(state, info) {
      Object.assign(state, getDefaultState(), info)
    },
    RESET_STATE(state) {
      Object.assign(state, getDefaultState())
    },
  },

  actions: {
    /**
     * 登录
     *
     * 流程：
     *   1. 调用后端登录 API（POST /api/rbac/auth/login/）
     *   2. 后端设置 Session（返回 Cookie）
     *   3. 立即获取用户信息（包含权限码）
     *   4. 提交 mutation 更新 state
     */
    async login({ commit, dispatch }, { username, password }) {
      const success = await apiLogin({ username, password })
      if (success) {
        // 登录成功后获取完整用户信息
        await dispatch('getUserInfo')
      }
      return success
    },

    /**
     * 获取当前用户信息
     *
     * 什么时候调用？
     *   —— 登录成功后（补充完整信息）
     *   —— 页面刷新时（从 Session 恢复用户状态）
     *   —— 路由守卫 beforeEach 中（验证 Session 是否有效）
     */
    async getUserInfo({ commit }) {
      try {
        const res = await apiGetUserInfo()
        commit('SET_USER_INFO', {
          id: res.id,
          username: res.username,
          email: res.email || '',
          is_superuser: res.is_superuser || false,
          roles: res.roles || [],
          permissions: res.permissions || [],
          primary_organization: res.primary_organization || null,
        })
        return true
      } catch (e) {
        console.error('[user store] getUserInfo failed:', e)
        return false
      }
    },

    /**
     * 登出
     */
    async logout({ commit }) {
      try {
        await apiLogout()
      } catch (e) {
        // 登出 API 失败也清除本地状态
      }
      // 清除 Vuex state
      commit('RESET_STATE')
      // 清除 Vuex menu state
      commit('menu/SET_MENU_TREE', [], { root: true })
    },
  },
}
