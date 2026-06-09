/** 角色管理 — 前端类型契约 v1.0 */

/** 角色输出 */
export interface RoleOutput {
    id: number
    name: string
    code: string
    description: string
    is_unique: boolean
    user_count: number
    created_at: string
    updated_at: string
}

/** 创建角色输入 */
export interface RoleCreateInput {
    name: string
    code: string
    description?: string
    is_unique?: boolean
}

/** 更新角色输入（全可选） */
export interface RoleUpdateInput {
    name?: string
    code?: string
    description?: string
    is_unique?: boolean
}
