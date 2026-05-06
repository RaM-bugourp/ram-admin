/**
 * 菜单 Store
 *
 * 负责：从后端获取菜单树，转发给路由系统
 *
 * 为什么菜单要单独一个 store？
 *   —— 菜单树在多个地方用到：侧边栏渲染、路由生成、面包屑
 *   —— 页面刷新后需要重新获取（存 Vuex 不够，需要从后端拉取）
 */

import { getMenuTree } from '@/api/menu'

export default {
  namespaced: true,

  state: () => ({
    // 菜单树（后端返回的原始结构）
    menuTree: [],
    // 是否已加载
    loaded: false,
  }),

  getters: {
    // 扁平化为路由数组（用于权限校验等）
    flatMenuList: (state) => _flattenMenu(state.menuTree),
  },

  mutations: {
    SET_MENU_TREE(state, tree) {
      state.menuTree = tree
      state.loaded = true
    },
    RESET_STATE(state) {
      state.menuTree = []
      state.loaded = false
    },
  },

  actions: {
    /**
     * 获取菜单树
     *
     * 注意：此 API 在路由守卫中被调用，不应在组件重复调用
     */
    async getMenuTree({ commit }) {
      try {
        const res = await getMenuTree()
        commit('SET_MENU_TREE', res || [])
        return true
      } catch (e) {
        console.error('[menu store] getMenuTree failed:', e)
        commit('SET_MENU_TREE', [])
        return false
      }
    },
  },
}

/**
 * 递归扁平化菜单树（内部函数）
 *
 * 为什么需要扁平化？
 *   —— 某些场景需要遍历所有菜单（如权限校验）
 *   —— 扁平化后可以用 Set 快速查找
 */
function _flattenMenu(tree, result = []) {
  for (const item of tree) {
    result.push(item)
    if (item.children?.length > 0) {
      _flattenMenu(item.children, result)
    }
  }
  return result
}
