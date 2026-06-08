/** 用户管理 — 前端类型契约 v1.0 */

/** 用户输出 */
export interface UserOutput {
    id: number
    username: string
    email: string
    is_active: boolean
    is_superuser: boolean
    roles: { id: number; name: string; code: string }[]
    created_at: string
    updated_at: string
}

/** 创建用户输入 */
export interface UserCreateInput {
    username: string
    email: string
    password: string
    is_active?: boolean
    role_ids?: number[]
}

/** 更新用户输入（全可选） */
export interface UserUpdateInput {
    username?: string
    email?: string
    is_active?: boolean
    role_ids?: number[]
}

/** 重置密码输入 */
export interface UserResetPasswordInput {
    password: string
}

/** 列表分页 */
export interface PaginationInfo {
    page: number
    page_size: number
    total: number
    total_pages: number
}

/** 列表响应 */
export interface UserListResponse {
    data: UserOutput[]
    pagination: PaginationInfo
}
