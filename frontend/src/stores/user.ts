import { Module } from 'vuex'
import client from '@/api/client'

interface RoleInfo {
    id: number
    name: string
    code: string
}

interface UserState {
    currentUser: { id: number; username: string; email: string } | null
    roles: RoleInfo[]
    permissions: string[]
}

const ADMIN_ROLES = ['root', 'boss']

const user: Module<UserState, any> = {
    namespaced: true,
    state: (): UserState => ({
        currentUser: null,
        roles: [],
        permissions: [],
    }),
    getters: {
        isAuthenticated(state: UserState): boolean {
            return !!state.currentUser
        },
        /** 是否具有管理员角色（root 或 boss） */
        isAdmin(state: UserState): boolean {
            return state.roles.some((r: RoleInfo) => ADMIN_ROLES.includes(r.code))
        },
        /** 是否为 root 角色（用于 AI 功能鉴权） */
        isRoot(state: UserState): boolean {
            return state.roles.some((r: RoleInfo) => r.code === 'root')
        },
        /** 角色编码列表 */
        roleCodes(state: UserState): string[] {
            return state.roles.map((r: RoleInfo) => r.code)
        },
    },
    mutations: {
        SET_USER(state: UserState, user: any) {
            state.currentUser = user
        },
        SET_ROLES(state: UserState, roles: RoleInfo[]) {
            state.roles = roles
        },
        SET_PERMISSIONS(state: UserState, permissions: string[]) {
            state.permissions = permissions
        },
        CLEAR(state: UserState) {
            state.currentUser = null
            state.roles = []
            state.permissions = []
        },
    },
    actions: {
        async login({ commit }: any, { username, password }: { username: string; password: string }) {
            const res: any = await client.post('/auth/login/', { username, password })
            // axios 拦截器已解包 response.data，res 就是 { data: { ... } }
            const userData = res.data || res
            commit('SET_USER', userData)
            commit('SET_ROLES', userData?.roles || [])
            commit('SET_PERMISSIONS', [])
        },
        async fetchUserInfo({ commit }: any) {
            const res: any = await client.get('/auth/user-info/')
            // axios 拦截器已解包 response.data，res 就是 { data: { ... } }
            const userData = res.data || res
            commit('SET_USER', userData)
            commit('SET_ROLES', userData?.roles || [])
            commit('SET_PERMISSIONS', userData?.permissions || [])
        },
        async logout({ commit }: any) {
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
