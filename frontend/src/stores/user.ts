import { Module } from 'vuex'
import client from '@/api/client'

interface UserState {
    currentUser: { id: number; username: string; email: string } | null
    permissions: string[]
}

const user: Module<UserState, any> = {
    namespaced: true,
    state: (): UserState => ({
        currentUser: null,
        permissions: [],
    }),
    getters: {
        isAuthenticated(state): boolean {
            return !!state.currentUser
        },
    },
    mutations: {
        SET_USER(state, user) {
            state.currentUser = user
        },
        SET_PERMISSIONS(state, permissions: string[]) {
            state.permissions = permissions
        },
        CLEAR(state) {
            state.currentUser = null
            state.permissions = []
        },
    },
    actions: {
        async login({ dispatch }, { username, password }: { username: string; password: string }) {
            await client.post('/auth/login/', { username, password })
            await dispatch('fetchUserInfo')
        },
        async fetchUserInfo({ commit }) {
            const res: any = await client.get('/auth/user-info/')
            commit('SET_USER', res.data)
            commit('SET_PERMISSIONS', res.data?.permissions || [])
        },
        async logout({ commit }) {
            try {
                await client.post('/auth/logout/')
            } catch {
                /* ignore */
            }
            commit('CLEAR')
        },
    },
}

export default user
