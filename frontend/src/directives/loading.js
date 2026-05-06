/**
 * Loading 指令
 * =============================================================
 *
 * 用法：
 *   <div v-loading="loading">内容</div>
 *   <div v-loading.fullscreen="loading">全屏遮罩</div>
 */

import { createApp, h } from 'vue'
import { Spin } from '@arco-design/web-vue'

const loadingMap = new WeakMap()

export const loading = {
  mounted(el, binding) {
    const value = !!binding.value
    const fullscreen = binding.modifiers.fullscreen

    if (value) {
      _showLoading(el, fullscreen)
    }
  },

  updated(el, binding) {
    const value = !!binding.value
    const fullscreen = binding.modifiers.fullscreen
    const instance = loadingMap.get(el)

    if (value && !instance) {
      _showLoading(el, fullscreen)
    } else if (!value && instance) {
      _hideLoading(el)
    }
  },

  unmounted(el) {
    _hideLoading(el)
  },
}

function _showLoading(el, fullscreen) {
  // 创建遮罩容器
  const container = document.createElement('div')
  container.className = 'v-loading-container'
  container.style.cssText = `
    position: ${fullscreen ? 'fixed' : 'absolute'};
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: ${fullscreen ? 9999 : 100};
  `

  // 创建 Spin 组件
  const app = createApp({
    render: () => h(Spin, { size: 32 }),
  })
  app.mount(container)

  el.style.position = el.style.position || 'relative'
  el.appendChild(container)

  loadingMap.set(el, container)
}

function _hideLoading(el) {
  const container = loadingMap.get(el)
  if (container) {
    container.remove()
    loadingMap.delete(el)
  }
}

/**
 * 注册指令
 */
export function setupLoadingDirective(app) {
  app.directive('loading', loading)
}
