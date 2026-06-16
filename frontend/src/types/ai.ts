/** AI 模块 — 前端类型契约 v1.0 */

/** 对话消息 */
export interface AIMessage {
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp?: string
}

/** 对话请求 */
export interface AIChatRequest {
    messages: AIMessage[]
    context?: string
    stream?: boolean
    agent_mode?: boolean
}

/** 对话响应 */
export interface AIChatResponse {
    reply: string
    provider_used: string
    failover_triggered: boolean
    call_id: string
    data?: any[]
}

/** Provider 状态 */
export interface AIProviderItem {
    name: string
    model?: string
    status: 'healthy' | 'degraded' | 'failed'
    failures: number
}

export interface AIProviderStatus {
    providers: AIProviderItem[]
    current_provider: string
    failover_triggered: boolean
    mock_mode: boolean
}

/** 洞察 */
export interface AIInsight {
    insight: string
    level: 'info' | 'warning' | 'danger' | string
}

export interface AIInsightsResponse {
    insights: AIInsight[]
    raw: string
    provider_used: string
    call_id: string
}

/** 分析 */
export interface AIAnalyzeResponse {
    reply: string
    provider_used: string
    failover_triggered: boolean
    call_id: string
    data?: Record<string, any>
}

/** 报告 */
export interface AIReportResponse {
    report: string
    report_type: string
    provider_used: string
    call_id: string
}

/** 审批 */
export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'timeout' | 'executed' | 'failed'

export interface AIApproval {
    id: number
    approval_uid: string
    agent_id: string
    operation: string
    params: Record<string, any>
    reason: string
    status: ApprovalStatus
    approved_by: number | null
    approved_by_name?: string
    approved_at: string | null
    approver_comment: string
    executed_at: string | null
    execution_error: string
    created_at: string
    updated_at: string
}

export interface AIApprovalListResponse {
    data: AIApproval[]
    pagination: {
        page: number
        page_size: number
        total: number
        total_pages: number
    }
}

export interface AIApprovalSubmitInput {
    agent_id: string
    operation: string
    params?: Record<string, any>
    reason?: string
}

export interface AIApprovalReviewInput {
    action: 'approve' | 'reject'
    comment?: string
}

/** 审计日志 */
export interface AICallLog {
    id: number
    call_id: string
    root_user: number | null
    root_user_name?: string
    agent_id: string
    call_type: string
    prompt: string
    response: string
    provider_used: string
    failover_triggered: boolean
    tokens_used: number | null
    cost: string | null
    ip_address: string | null
    created_at: string
}

export interface AICallLogListResponse {
    data: AICallLog[]
    pagination: {
        page: number
        page_size: number
        total: number
        total_pages: number
    }
}

export interface AIAuditSummary {
    total_calls: number
    calls_by_type: { call_type: string; count: number }[]
    failover_count: number
    pending_approvals: number
    approved: number
    rejected: number
}

/** 通知 */
export type NotificationLevel = 'info' | 'success' | 'warning' | 'error'

export interface AINotification {
    id: number
    title: string
    message: string
    level: NotificationLevel
    is_read: boolean
    created_at: string
}

export interface AINotificationListResponse {
    data: AINotification[]
    pagination: {
        page: number
        page_size: number
        total: number
        total_pages: number
    }
    unread_count: number
}

/** Agent Token */
export interface AgentTokenIssueInput {
    agent_id: string
    ttl_hours?: number
}

export interface AgentTokenIssueResponse {
    token: string
    agent_id: string
    expires_in_hours: number
    note: string
}
