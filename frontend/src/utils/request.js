/**
 * Axios 请求封装
 * =============================================================
 *
 * 功能：
 *   1. 请求拦截：自动携带 CSRF Token
 *   2. 响应拦截：统一错误处理、DRF 分页适配
 *   3. 支持取消请求
 */

import axios from 'axios'
import { Message } from '@arco-design/web-vue'

// 创建 axios 实例
const request = axios.create({
  baseURL: '/api',
  timeout: 10000,
  withCredentials: true, // 携带 cookie（Session 认证）
})

// ─────────────────────────────────────────────────────────────────
// 请求拦截器
// ─────────────────────────────────────────────────────────────────
request.interceptors.request.use(
  (config) => {
    // CSRF Token（Django 默认从 cookie 读取）
    const csrfToken = document.cookie
      .split('; ')
      .find((row) => row.startsWith('csrftoken='))
      ?.split('=')[1]

    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }

    return config
  },
  (error) => Promise.reject(error)
)

// ─────────────────────────────────────────────────────────────────
// 响应拦截器
// ─────────────────────────────────────────────────────────────────
request.interceptors.response.use(
  (response) => {
    // DRF 分页适配：返回 results 数组 + 分页信息
    const data = response.data
    if (data && Array.isArray(data.results)) {
      return {
        list: data.results,
        total: data.count,
        page: data.page || 1,
        totalPages: data.total_pages || Math.ceil(data.count / 10),
      }
    }
    return data
  },
  (error) => {
    const status = error.response?.status
    const data = error.response?.data

    // 统一错误提示
    if (status === 401) {
      Message.error('登录已过期，请重新登录')
      // 跳转登录页
      window.location.href = '/login'
    } else if (status === 403) {
      Message.error('没有权限执行此操作')
    } else if (status === 400) {
      // DRF 表单错误
      const msg = data?.detail || Object.values(data || {}).flat().join('; ')
      Message.error(msg || '请求参数错误')
    } else if (status === 500) {
      Message.error('服务器内部错误')
    } else {
      Message.error(data?.detail || error.message || '请求失败')
    }

    return Promise.reject(error)
  }
)

export default request
