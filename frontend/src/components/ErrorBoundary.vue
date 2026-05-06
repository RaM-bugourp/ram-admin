<template>
  <slot />
</template>

<script setup>
/**
 * 全局错误边界组件
 * =============================================================
 *
 * 捕获子组件的 JavaScript 错误，显示友好错误页面
 * 用法：<ErrorBoundary><router-view /></ErrorBoundary>
 */

import { onErrorCaptured, ref } from 'vue'
import { Message } from '@arco-design/web-vue'

const error = ref(null)

onErrorCaptured((err, instance, info) => {
  console.error('[ErrorBoundary]', err, info)
  
  error.value = err
  
  // 显示错误提示
  Message.error({
    content: `页面错误：${err.message}`,
    duration: 5000,
  })
  
  // 返回 false 阻止错误继续传播
  return false
})
</script>
