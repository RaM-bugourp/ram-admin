/**
 * Audit log API — list, stats, cleanup.
 */
import client from '@/api/client'

export interface AuditLogItem {
  id: number
  username: string
  action: string
  action_label: string
  resource: string
  resource_label: string
  resource_id: string | null
  detail: string
  ip_address: string | null
  user_agent: string
  extra_data: Record<string, unknown>
  created_at: string
}

export interface AuditStats {
  total: number
  by_action: Record<string, number>
  by_resource: Record<string, number>
  today: number
  today_login: number
}

export interface AuditListResponse {
  data: AuditLogItem[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

/** 审计日志列表 */
export async function getAuditLogs(params: {
  page?: number
  page_size?: number
  action?: string
  resource?: string
  username?: string
  start_date?: string
  end_date?: string
}): Promise<AuditListResponse> {
  return client.get('/audit/logs/', { params })
}

/** 审计统计 */
export async function getAuditStats(): Promise<{ data: AuditStats }> {
  return client.get('/audit/logs/stats/')
}

/** 清理过期日志 */
export async function cleanupAuditLogs(
  days: number = 90
): Promise<{ data: { deleted: number; cutoff_days: number } }> {
  return client.delete('/audit/logs/cleanup/', { params: { days } })
}

/** 操作类型选项 */
export async function getActionOptions(): Promise<
  { data: { value: string; label: string }[] }
> {
  return client.get('/audit/logs/actions/')
}

/** 资源类型选项 */
export async function getResourceOptions(): Promise<
  { data: { value: string; label: string }[] }
> {
  return client.get('/audit/logs/resources/')
}