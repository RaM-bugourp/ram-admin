import client from '../client'
import type { RoleCreateInput, RoleUpdateInput, RoleOutput } from '@/types/role'

export const roleApi = {
    /** 角色列表 */
    list: (): Promise<{ data: RoleOutput[] }> =>
        client.get('/rbac/roles/'),

    /** 角色详情 */
    getById: (id: number): Promise<{ data: RoleOutput }> =>
        client.get(`/rbac/roles/${id}/`),

    /** 创建角色 */
    create: (data: RoleCreateInput): Promise<{ data: RoleOutput }> =>
        client.post('/rbac/roles/', data),

    /** 更新角色 */
    update: (id: number, data: RoleUpdateInput): Promise<{ data: RoleOutput }> =>
        client.put(`/rbac/roles/${id}/`, data),

    /** 删除角色 */
    delete: (id: number): Promise<void> =>
        client.delete(`/rbac/roles/${id}/`),
}
