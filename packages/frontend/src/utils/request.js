/**
 * Axios 封装 —— HTTP 请求核心
 * =============================================================
 *
 * 本模块封装了所有后端 API 调用，特性：
 *   - 请求拦截：自动注入 Token / CSRF
 *   - 响应拦截：统一错误处理（401跳转登录、403权限拒绝）
 *   - 适配 DRF 标准响应格式 { count, results, next, previous }
 *
 * 设计思路：
 *   为什么不直接用 axios.get() ？
 *   —— 每次请求都要手动处理 Token 注入、错误处理、401 重定向
 *   —— 封装后：request(config) 自动完成所有通用逻辑
 *   —— 新接口只需调用 api.xxx()，不用关心底层细节
 */

import axios from 'axios'
import { Message } from '@arco-design/web-vue'
import router from '@/router'

// ─────────────────────────────────────────────────────────────────
// 1. 创建 axios 实例（可配置多个后端）
// ─────────────────────────────────────────────────────────────────

const request = axios.create({
  // 后端 API 基础地址
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',

  // 请求超时
  timeout: 30000,

  // 跨域请求允许携带 Cookie
  withCredentials: true,
})

// ─────────────────────────────────────────────────────────────────
// 2. 请求拦截器
// ─────────────────────────────────────────────────────────────────

request.interceptors.request.use(
  (config) => {
    /**
     * 自动注入认证信息
     *
     * 两种认证方式（根据后端配置选择）：
     *   1. Session 认证：Cookie 中的 sessionid（无感知）
     *   2. Token 认证：从 localStorage 取 token，手动加 header
     *
     * 本框架使用 Session 认证（DRF SessionAuthentication），
     * 所以不需要手动注入 Token，但保留 Token 注入逻辑备用。
     */
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    // 注入 CSRF Token（Django CSRF 保护需要）
    const csrfToken = _getCsrfToken()
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }

    return config
  },
  (error) => {
    // 请求配置错误（很少发生）
    return Promise.reject(error)
  }
)

// ─────────────────────────────────────────────────────────────────
// 3. 响应拦截器
// ─────────────────────────────────────────────────────────────────

request.interceptors.response.use(
  (response) => {
    /**
     * 成功响应处理
     *
     * DRF 标准分页响应：
     *   { count, next, previous, results }
     *
     * 非分页响应：
     *   直接返回 response.data
     *
     * 区分方式：检查是否有 results 字段
     */
    const data = response.data

    if (data && typeof data === 'object' && 'results' in data) {
      // 分页响应：返回 data（含 count/next/previous/results）
      return data
    }

    // 非分页响应：直接返回数据
    return data
  },

  (error) => {
    /**
     * 错误响应处理
     *
     * 错误分级：
     *   400  — 参数错误（业务逻辑错误，提示用户）
     *   401  — 未登录（跳转到登录页）
     *   403  — 无权限（提示用户没有权限）
     *   404  — 资源不存在
     *   500  — 服务器错误（告警通知）
     *   N    — 网络错误
     */

    if (error.response) {
      // 服务器已响应（有 status code）
      const { status, data } = error.response

      switch (status) {
        case 400:
          _handleBadRequest(data)
          break
        case 401:
          _handleUnauthorized()
          break
        case 403:
          _handleForbidden(data)
          break
        case 404:
          Message.warning('请求的资源不存在')
          break
        case 500:
          Message.error('服务器内部错误，请联系管理员')
          break
        default:
          Message.error(data?.detail || data?.message || `请求失败 (${status})`)
      }
    } else {
      // 网络错误（无响应）
      Message.error('网络连接失败，请检查网络')
    }

    return Promise.reject(error)
  }
)

// ─────────────────────────────────────────────────────────────────
// 4. 辅助函数
// ─────────────────────────────────────────────────────────────────

/**
 * 从 Cookie 中读取 CSRF Token
 *
 * Django 的 CSRF Token 存在 Cookie 中，名称是 csrftoken
 * 前端发 POST/PUT/PATCH/DELETE 请求时需要加到 header
 */
function _getCsrfToken() {
  const name = 'csrftoken'
  let token = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        token = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return token
}

/**
 * 401 处理：未登录，跳转登录页
 *
 * 注意：登录页本身不应该被拦截，否则会死循环。
 * 在 router.beforeEach 里，/login 路径会直接放行。
 */
function _handleUnauthorized() {
  // 清除本地用户状态
  localStorage.removeItem('access_token')
  // 提示并跳转
  Message.warning('登录已过期，请重新登录')
  if (router.currentRoute.path !== '/login') {
    router.push('/login')
  }
}

/**
 * 403 处理：无权限
 */
function _handleForbidden(data) {
  const msg = data?.detail || '您没有权限执行此操作'
  Message.error(msg)
}

/**
 * 400 处理：参数校验失败
 */
function _handleBadRequest(data) {
  // DRF 的校验错误格式：{ field_name: [error1, error2] }
  if (typeof data === 'object' && !data.detail) {
    const messages = Object.entries(data)
      .map(([field, errors]) => {
        const fieldLabel = field
        const msgs = Array.isArray(errors) ? errors.join(', ') : errors
        return `${fieldLabel}: ${msgs}`
      })
      .join('; ')
    Message.error(messages || '参数错误')
  } else {
    Message.error(data?.detail || '请求参数错误')
  }
}

// ─────────────────────────────────────────────────────────────────
// 5. 导出
// ─────────────────────────────────────────────────────────────────

export default request

/**
 * 标准 API 调用方式（推荐）
 *
 * 每个业务模块创建一个文件，如 api/article.js：
 *
 *   import request from '@/utils/request'
 *
 *   export const getArticleList = (params) => request.get('/article/', { params })
 *   export const getArticleDetail = (id) => request.get(`/article/${id}/`)
 *   export const createArticle = (data) => request.post('/article/', data)
 *   export const updateArticle = (id, data) => request.put(`/article/${id}/`, data)
 *   export const deleteArticle = (id) => request.delete(`/article/${id}/`)
 *
 * 为什么每个方法单独导出而不是统一封装？
 *   —— 更灵活，可以自定义参数和错误处理
 *   —— 语义清晰：getArticleList，一看就知道是获取列表
 *   —— TypeScript 友好，可以给每个方法加类型
 */
