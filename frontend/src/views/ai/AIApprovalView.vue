<template>
    <div class="approval-page">
        <div class="toolbar">
            <a-radio-group v-model="statusFilter" @change="handleFilterChange" type="button">
                <a-radio value="">全部</a-radio>
                <a-radio value="pending">待审批</a-radio>
                <a-radio value="approved">已通过</a-radio>
                <a-radio value="rejected">已拒绝</a-radio>
                <a-radio value="executed">已执行</a-radio>
                <a-radio value="failed">执行失败</a-radio>
            </a-radio-group>
            <a-button @click="fetchList" :loading="loading">
                <template #icon><icon-refresh /></template>
                刷新
            </a-button>
        </div>

        <a-table
            :columns="columns"
            :data="tableData"
            :loading="loading"
            :pagination="pagination"
            row-key="id"
            @page-change="handlePageChange"
        >
            <template #agent_id="{ record }">
                <a-tag color="arcoblue">{{ record.agent_id }}</a-tag>
            </template>
            <template #operation="{ record }">
                <a-tag>{{ record.operation }}</a-tag>
            </template>
            <template #params="{ record }">
                <a-typography-text ellipsis style="max-width: 280px">
                    <code>{{ JSON.stringify(record.params) }}</code>
                </a-typography-text>
            </template>
            <template #status="{ record }">
                <a-tag :color="statusColor(record.status)">
                    {{ statusLabel(record.status) }}
                </a-tag>
            </template>
            <template #created_at="{ record }">
                {{ formatTime(record.created_at) }}
            </template>
            <template #actions="{ record }">
                <a-space v-if="record.status === 'pending'">
                    <a-button type="primary" size="small" @click="openReview(record, 'approve')">
                        通过
                    </a-button>
                    <a-button status="danger" size="small" @click="openReview(record, 'reject')">
                        拒绝
                    </a-button>
                </a-space>
                <a-button v-else size="small" @click="openDetail(record)">详情</a-button>
            </template>
        </a-table>

        <!-- 审批弹窗 -->
        <a-modal
            :visible="reviewVisible"
            :title="reviewAction === 'approve' ? '通过审批' : '拒绝审批'"
            @ok="confirmReview"
            @cancel="reviewVisible = false"
            :ok-button-props="{ status: reviewAction === 'approve' ? 'success' : 'danger' }"
        >
            <div v-if="currentApproval" class="review-content">
                <a-descriptions :column="1" size="small" bordered>
                    <a-descriptions-item label="Agent">{{ currentApproval.agent_id }}</a-descriptions-item>
                    <a-descriptions-item label="操作">{{ currentApproval.operation }}</a-descriptions-item>
                    <a-descriptions-item label="参数">
                        <code>{{ JSON.stringify(currentApproval.params) }}</code>
                    </a-descriptions-item>
                    <a-descriptions-item label="原因">{{ currentApproval.reason || '-' }}</a-descriptions-item>
                </a-descriptions>
                <a-form layout="vertical" style="margin-top: 16px">
                    <a-form-item label="审批备注">
                        <a-textarea
                            v-model="reviewComment"
                            placeholder="填写审批意见（可选）"
                            :auto-size="{ minRows: 2, maxRows: 4 }"
                        />
                    </a-form-item>
                </a-form>
            </div>
        </a-modal>

        <!-- 详情弹窗 -->
        <a-modal
            :visible="detailVisible"
            title="审批详情"
            width="640px"
            :footer="false"
            @cancel="detailVisible = false"
        >
            <a-descriptions v-if="currentApproval" :column="1" bordered>
                <a-descriptions-item label="Agent">{{ currentApproval.agent_id }}</a-descriptions-item>
                <a-descriptions-item label="操作">{{ currentApproval.operation }}</a-descriptions-item>
                <a-descriptions-item label="参数">
                    <code>{{ JSON.stringify(currentApproval.params, null, 2) }}</code>
                </a-descriptions-item>
                <a-descriptions-item label="原因">{{ currentApproval.reason || '-' }}</a-descriptions-item>
                <a-descriptions-item label="状态">
                    <a-tag :color="statusColor(currentApproval.status)">{{ statusLabel(currentApproval.status) }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="审批人">{{ currentApproval.approved_by_name || '-' }}</a-descriptions-item>
                <a-descriptions-item label="审批时间">{{ formatTime(currentApproval.approved_at) }}</a-descriptions-item>
                <a-descriptions-item label="审批备注">{{ currentApproval.approver_comment || '-' }}</a-descriptions-item>
                <a-descriptions-item label="执行时间">{{ formatTime(currentApproval.executed_at) }}</a-descriptions-item>
                <a-descriptions-item label="执行错误" v-if="currentApproval.execution_error">
                    <span style="color: rgb(var(--danger-6))">{{ currentApproval.execution_error }}</span>
                </a-descriptions-item>
            </a-descriptions>
        </a-modal>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconRefresh } from '@arco-design/web-vue/es/icon'
import { aiApi } from '@/api/modules/ai'
import type { AIApproval, ApprovalStatus } from '@/types/ai'

const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: 'Agent', slotName: 'agent_id', width: 120 },
    { title: '操作', slotName: 'operation', width: 130 },
    { title: '参数', slotName: 'params', ellipsis: true },
    { title: '原因', dataIndex: 'reason', ellipsis: true, width: 180 },
    { title: '状态', slotName: 'status', width: 100 },
    { title: '提交时间', slotName: 'created_at', width: 160 },
    { title: '操作', slotName: 'actions', width: 160, fixed: 'right' as const },
]

const loading = ref(false)
const tableData = ref<AIApproval[]>([])
const statusFilter = ref('')
const currentPage = ref(1)

const pagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0,
    showTotal: true,
})

const reviewVisible = ref(false)
const detailVisible = ref(false)
const currentApproval = ref<AIApproval | null>(null)
const reviewAction = ref<'approve' | 'reject'>('approve')
const reviewComment = ref('')

const STATUS_MAP: Record<ApprovalStatus, { label: string; color: string }> = {
    pending: { label: '待审批', color: 'orange' },
    approved: { label: '已通过', color: 'green' },
    rejected: { label: '已拒绝', color: 'red' },
    timeout: { label: '已超时', color: 'gray' },
    executed: { label: '已执行', color: 'arcoblue' },
    failed: { label: '执行失败', color: 'red' },
}

function statusLabel(s: ApprovalStatus): string {
    return STATUS_MAP[s]?.label || s
}
function statusColor(s: ApprovalStatus): string {
    return STATUS_MAP[s]?.color || 'gray'
}

async function fetchList() {
    loading.value = true
    try {
        const res = await aiApi.listApprovals({
            status: statusFilter.value || undefined,
            page: currentPage.value,
        })
        tableData.value = res.data
        pagination.total = res.pagination.total
        pagination.current = res.pagination.page
    } catch (e: any) {
        Message.error(e.message || '加载失败')
    } finally {
        loading.value = false
    }
}

function handleFilterChange() {
    currentPage.value = 1
    fetchList()
}

function handlePageChange(page: number) {
    currentPage.value = page
    fetchList()
}

function openReview(record: AIApproval, action: 'approve' | 'reject') {
    currentApproval.value = record
    reviewAction.value = action
    reviewComment.value = ''
    reviewVisible.value = true
}

function openDetail(record: AIApproval) {
    currentApproval.value = record
    detailVisible.value = true
}

async function confirmReview() {
    if (!currentApproval.value) return
    try {
        await aiApi.reviewApproval(currentApproval.value.id, {
            action: reviewAction.value,
            comment: reviewComment.value,
        })
        Message.success(reviewAction.value === 'approve' ? '已通过' : '已拒绝')
        reviewVisible.value = false
        fetchList()
    } catch (e: any) {
        Message.error(e.message || '操作失败')
    }
}

function formatTime(iso: string | null): string {
    if (!iso) return '-'
    const d = new Date(iso)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(fetchList)
</script>

<style scoped>
.approval-page {
    padding: 4px;
}
.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.review-content code {
    display: block;
    background: var(--color-fill-2);
    padding: 6px 10px;
    border-radius: 4px;
    font-family: 'Consolas', monospace;
    font-size: 13px;
    white-space: pre-wrap;
    word-break: break-all;
}
</style>
