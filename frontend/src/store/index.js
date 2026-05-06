/**
 * Vuex Store — 根模块
 */

import Vuex from 'vuex'
import createPersistedState from 'vuex-persistedstate'
import user from './modules/user'
import menu from './modules/menu'

const store = new Vuex.Store({
  modules: { user, menu },
  strict: process.env.NODE_ENV !== 'production',
  plugins: [
    // 状态持久化到 localStorage
    createPersistedState({
      key: 'ram-admin-state',
      paths: ['user.id', 'user.username', 'user.is_superuser', 'user.roles', 'user.permissions'],
      storage: window.localStorage,
    }),
  ],
})

export default store
