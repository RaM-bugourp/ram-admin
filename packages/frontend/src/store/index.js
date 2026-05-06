/**
 * Vuex Store 根模块
 *
 * 导出方式：
 *   import store from '@/store'
 *   store.dispatch('user/login', formData)
 *   store.getters['user/hasPermission']('article:list')
 */

import Vuex from 'vuex'
import user from './modules/user'
import menu from './modules/menu'

const store = new Vuex.Store({
  modules: {
    user,
    menu,
  },

  // 严格模式（禁止直接修改 state，强制通过 mutation）
  strict: process.env.NODE_ENV !== 'production',
})

export default store
