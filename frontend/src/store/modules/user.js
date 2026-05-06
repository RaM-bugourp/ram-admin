/**
 * 用户认证 Store
 */

import * as api from '@/api/user'

const getDefaultState = () => ({
  id: null,
  username: '',
  email: '',
  is_superuser: false,
  roles: [],
  permissions: [],
})

export default {
  namespaced: true,
  state: getDefaultState(),

  getters: {
    hasPermission: (state) => (code) => {
      if (state.is_superuser) return true
      return state.permissions.includes(code)
    },
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
    async login({ commit, dispatch }, { username, password }) {
      await api.login({ username, password })
      await dispatch('getUserInfo')
      return true
    },

    async getUserInfo({ commit }) {
      const res = await api.getUserInfo()
      commit('SET_USER_INFO', {
        id: res.id,
        username: res.username,
        email: res.email || '',
        is_superuser: res.is_superuser || false,
        roles: res.roles || [],
        permissions: res.permission_codes || [],
      })
      window.__userId__ = res.id
      window.__userInfo__ = res
      return true
    },

    async logout({ commit }) {
      try { await api.logout() } catch {}
      commit('RESET_STATE')
      commit('menu/SET_MENU_TREE', [], { root: true })
      delete window.__userId__
      delete window.__userInfo__
    },
  },
}
