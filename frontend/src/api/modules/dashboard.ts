import client from '../client'

export interface DashboardStats {
    total_users: number
    active_users: number
    total_roles: number
    total_assignments: number
}

export const dashboardApi = {
    /** 获取仪表盘统计数据 */
    getStats: () =>
        client.get<any, { data: DashboardStats }>('/dashboard/stats/'),
}
