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

client.interceptors.response.use(
    (response) => response.data,
    (error: AxiosError<{ error?: { code: string; message: string } }>) => {
        const status = error.response?.status
        if (status === 401) {
            store.dispatch('user/logout')
            router.push('/login')
        }
        if (status === 403) {
            router.push('/403')
        }
        return Promise.reject({
            code: error.response?.data?.error?.code || 'UNKNOWN',
            message: error.response?.data?.error?.message || '请求失败',
            status,
        })
    },
)

export default client
