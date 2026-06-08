import client from '../client'
import type { UserCreateInput, UserUpdateInput, UserOutput, UserListResponse, UserResetPasswordInput } from '@/types/user'

export const userApi = {
    /** 用户列表（分页 + 搜索） */
    list: (params: { page?: number; page_size?: number; search?: string } = {}): Promise<UserListResponse> =>
        client.get('/rbac/users/', { params }),

    /** 用户详情 */
    getById: (id: number): Promise<{ data: UserOutput }> =>
        client.get(`/rbac/users/${id}/`),

    /** 创建用户 */
    create: (data: UserCreateInput): Promise<{ data: UserOutput }> =>
        client.post('/rbac/users/', data),

    /** 更新用户 */
    update: (id: number, data: UserUpdateInput): Promise<{ data: UserOutput }> =>
        client.put(`/rbac/users/${id}/`, data),

    /** 删除用户（软删除） */
    delete: (id: number): Promise<void> =>
        client.delete(`/rbac/users/${id}/`),

    /** 重置密码 */
    resetPassword: (id: number, data: UserResetPasswordInput): Promise<{ data: { message: string } }> =>
        client.post(`/rbac/users/${id}/reset-password/`, data),
}
