import { Module } from 'vuex'
import { aiApi } from '@/api/modules/ai'
import type { AIProviderStatus } from '@/types/ai'

interface AIState {
    providerStatus: AIProviderStatus | null
    unreadNotifications: number
    providerStatusLoaded: boolean
}

const ai: Module<AIState, any> = {
    namespaced: true,
    state: (): AIState => ({
        providerStatus: null,
        unreadNotifications: 0,
        providerStatusLoaded: false,
    }),
    getters: {
        isFailoverActive(state: AIState): boolean {
            return !!state.providerStatus?.failover_triggered
        },
        isMockMode(state: AIState): boolean {
            return !!state.providerStatus?.mock_mode
        },
        hasUnread(state: AIState): boolean {
            return state.unreadNotifications > 0
        },
    },
    mutations: {
        SET_PROVIDER_STATUS(state: AIState, status: AIProviderStatus) {
            state.providerStatus = status
            state.providerStatusLoaded = true
        },
        SET_UNREAD(state: AIState, count: number) {
            state.unreadNotifications = count
        },
        DEC_UNREAD(state: AIState) {
            if (state.unreadNotifications > 0) state.unreadNotifications -= 1
        },
    },
    actions: {
        async fetchProviderStatus({ commit, rootGetters }) {
            // 仅 root 用户才请求
            if (!rootGetters['user/isRoot']) return
            try {
                const res: any = await aiApi.getProviderStatus()
                commit('SET_PROVIDER_STATUS', res.data)
            } catch {
                /* 静默 — 权限不足或网络错误不阻塞 UI */
            }
        },
        async fetchUnreadCount({ commit, rootGetters }) {
            if (!rootGetters['user/isRoot']) return
            try {
                const res: any = await aiApi.listNotifications({ unread: true, page_size: 1 })
                commit('SET_UNREAD', res.unread_count || 0)
            } catch {
                /* 静默 */
            }
        },
    },
}

export default ai
