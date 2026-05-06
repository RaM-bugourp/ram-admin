/**
 * 菜单 Store
 */

import * as api from '@/api/menu'

const getDefaultState = () => ({
  menuTree: [],
  flatMenuList: [],
  currentMenu: null,
})

export default {
  namespaced: true,
  state: getDefaultState(),

  getters: {
    menuTree: (state) => state.menuTree,
    flatMenuList: (state) => state.flatMenuList,
    sidebarMenu: (state) => {
      // 侧边栏菜单（过滤隐藏项）
      const filterHidden = (menus) => {
        return menus
          .filter((m) => !m.isHidden)
          .map((m) => ({
            ...m,
            children: m.children ? filterHidden(m.children) : [],
          }))
      }
      return filterHidden(state.menuTree)
    },
  },

  mutations: {
    SET_MENU_TREE(state, tree) {
      state.menuTree = tree
      // 扁平化菜单列表（用于权限检查）
      const flat = []
      const flatten = (menus, parentPath = '') => {
        menus.forEach((m) => {
          const path = parentPath + '/' + (m.path || '').replace(/^\/+/, '')
          flat.push({ ...m, fullPath: path })
          if (m.children?.length) flatten(m.children, path)
        })
      }
      flatten(tree)
      state.flatMenuList = flat
    },
    SET_CURRENT_MENU(state, menu) {
      state.currentMenu = menu
    },
    RESET_STATE(state) {
      Object.assign(state, getDefaultState())
    },
  },

  actions: {
    async getMenuTree({ commit }) {
      const res = await api.getMenuTree()
      commit('SET_MENU_TREE', res)
      return res
    },
  },
}
