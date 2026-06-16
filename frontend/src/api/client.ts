import axios, { AxiosError } from 'axios'
import router from '@/router'
import store from '@/stores'

const client = axios.create({
    baseURL: '/api',
    timeout: 15000,
    headers: { 'Content-Type': 'application/json' },
    withCredentials: true,
    xsrfCookieName: 'csrftoken',
    xsrfHeaderName: 'X-CSRFToken',
})

// 防止 401 递归：logout 本身也要发请求，若也返回 401 会死循环
let isLoggingOut = false

client.interceptors.response.use(
    (response) => response.data,
    (error: AxiosError<{ error?: { code: string; message: string } }>) => {
        const status = error.response?.status
        if (status === 401) {
            // 已登录用户才需要清理状态并跳转登录页
            if (store.getters['user/isAuthenticated'] && !isLoggingOut) {
                isLoggingOut = true
                store.dispatch('user/logout').finally(() => { isLoggingOut = false })
                router.push('/login')
            } else if (!store.getters['user/isAuthenticated']) {
                // 未登录用户的 401（如登录接口返回 401）只跳登录页，不 dispatch logout
                router.push('/login')
            }
        }
        if (status === 403) {
            // CSRF failure 也返回 403，但不应跳走——让调用方自行处理
            // 只有已登录用户访问无权限资源时才跳 403 页面
            if (store.getters['user/isAuthenticated']) {
                router.push('/403')
            }
        }
        return Promise.reject({
            code: error.response?.data?.error?.code || 'UNKNOWN',
            message: error.response?.data?.error?.message || '请求失败',
            status,
        })
    },
)

export default client
