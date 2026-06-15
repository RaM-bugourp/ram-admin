import client from '../client'
import type {
    AIChatRequest,
    AIChatResponse,
    AIProviderStatus,
    AIInsightsResponse,
    AIAnalyzeResponse,
    AIReportResponse,
    AIApproval,
    AIApprovalListResponse,
    AIApprovalSubmitInput,
    AIApprovalReviewInput,
    AICallLogListResponse,
    AIAuditSummary,
    AINotificationListResponse,
    AgentTokenIssueInput,
    AgentTokenIssueResponse,
} from '@/types/ai'

export const aiApi = {
    // ── 对话 ──────────────────────────────────────────
    chat: (data: AIChatRequest): Promise<{ data: AIChatResponse }> =>
        client.post('/ai/chat/chat/', data),

    getProviderStatus: (): Promise<{ data: AIProviderStatus }> =>
        client.get('/ai/chat/provider-status/'),

    // ── 分析 / 洞察 / 报告 ────────────────────────────
    analyze: (question: string): Promise<{ data: AIAnalyzeResponse }> =>
        client.post('/ai/analyze/analyze/', { question }),

    getInsights: (): Promise<{ data: AIInsightsResponse }> =>
        client.get('/ai/analyze/insights/'),

    generateReport: (reportType: string): Promise<{ data: AIReportResponse }> =>
        client.post('/ai/report/report/', { report_type: reportType }),

    // ── 审批 ──────────────────────────────────────────
    submitApproval: (data: AIApprovalSubmitInput): Promise<{ data: AIApproval }> =>
        client.post('/ai/approval/submit/', data),

    listApprovals: (params: { status?: string; agent_id?: string; page?: number; page_size?: number } = {}): Promise<AIApprovalListResponse> =>
        client.get('/ai/approval/', { params }),

    getApproval: (id: number): Promise<{ data: AIApproval }> =>
        client.get(`/ai/approval/${id}/`),

    reviewApproval: (id: number, data: AIApprovalReviewInput): Promise<{ data: AIApproval }> =>
        client.post(`/ai/approval/${id}/review/`, data),

    // ── 审计 ──────────────────────────────────────────
    listAuditLogs: (params: { start_date?: string; end_date?: string; call_type?: string; agent_id?: string; page?: number; page_size?: number } = {}): Promise<AICallLogListResponse> =>
        client.get('/ai/audit/', { params }),

    getAuditSummary: (): Promise<{ data: AIAuditSummary }> =>
        client.get('/ai/audit/summary/'),

    // ── 通知 ──────────────────────────────────────────
    listNotifications: (params: { unread?: boolean; page?: number; page_size?: number } = {}): Promise<AINotificationListResponse> =>
        client.get('/ai/notifications/', { params }),

    markNotificationRead: (id: number): Promise<{ data: { id: number; is_read: boolean } }> =>
        client.post(`/ai/notifications/${id}/read/`),

    markAllNotificationsRead: (): Promise<{ data: { updated: number } }> =>
        client.post('/ai/notifications/read-all/'),

    // ── Agent Token ───────────────────────────────────
    issueAgentToken: (data: AgentTokenIssueInput): Promise<{ data: AgentTokenIssueResponse }> =>
        client.post('/ai/agent-token/issue/', data),
}
