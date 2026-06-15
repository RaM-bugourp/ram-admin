<template>
    <div class="audit-page">
        <!-- 摘要卡片 -->
        <a-row :gutter="16" class="summary-row">
            <a-col :span="4">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-value">{{ summary?.total_calls ?? '...' }}</div>
                    <div class="stat-title">总调用数</div>
                </a-card>
            </a-col>
            <a-col :span="4">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-value" :class="{ 'warn': (summary?.failover_count ?? 0) > 0 }">
                        {{ summary?.failover_count ?? '...' }}
                    </div>
                    <div class="stat-title">故障转移次数</div>
                </a-card>
            </a-col>
            <a-col :span="4">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-value" :class="{ 'warn': (summary?.pending_approvals ?? 0) > 0 }">
                        {{ summary?.pending_approvals ?? '...' }}
                    </div>
                    <div class="stat-title">待审批</div>
                </a-card>
            </a-col>
            <a-col :span="4">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-value ok">{{ summary?.approved ?? '...' }}</div>
                    <div class="stat-title">已通过</div>
                </a-card>
            </a-col>
            <a-col :span="4">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-value danger">{{ summary?.rejected ?? '...' }}</div>
                    <div class="stat-title">已拒绝</div>
                </a-card>
            </a-col>
            <a-col :span="4">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-title" style="margin-top: 8px">调用类型分布</div>
                    <div class="type-list">
                        <a-tag v-for="t in summary?.calls_by_type || []" :key="t.call_type" size="small">
                            {{ t.call_type }}: {{ t.count }}
                        </a-tag>
                    </div>
                </a-card>
            </a-col>
        </a-row>

        <!-- 筛选 -->
        <div class="toolbar">
            <a-space>
                <a-select v-model="filter.call_type" placeholder="调用类型" allow-clear style="width: 160px">
                    <a-option value="chat">chat</a-option>
                    <a-option value="analyze">analyze</a-option>
                    <a-option value="report">report</a-option>
                    <a-option value="agent_submission">agent_submission</a-option>
                    <a-option value="agent_token_issue">agent_token_issue</a-option>
                </a-select>
                <a-input v-model="filter.agent_id" placeholder="Agent ID" allow-clear style="width: 180px" />
                <a-range-picker v-model="filter.dateRange" style="width: 240px" />
                <a-button type="primary" @click="handleSearch">
                    <template #icon><icon-search /></template>
                    查询
                </a-button>
                <a-button @click="resetFilter">重置</a-button>
            </a-space>
            <a-button @click="fetchData" :loading="loading">
                <template #icon><icon-refresh /></template>
                刷新
            </a-button>
        </div>

        <!-- 表格 -->
        <a-table
            :columns="columns"
            :data="tableData"
            :loading="loading"
            :pagination="pagination"
            row-key="id"
            @page-change="handlePageChange"
        >
            <template #root_user_name="{ record }">
                <a-tag v-if="record.root_user_name" color="green">{{ record.root_user_name }}</a-tag>
                <span v-else class="text-muted">-</span>
            </template>
            <template #agent_id="{ record }">
                <a-tag v-if="record.agent_id" color="arcoblue">{{ record.agent_id }}</a-tag>
                <span v-else class="text-muted">-</span>
            </template>
            <template #call_type="{ record }">
                <a-tag>{{ record.call_type }}</a-tag>
            </template>
            <template #prompt="{ record }">
                <a-typography-text ellipsis style="max-width: 260px" :tooltip="record.prompt">
                    {{ record.prompt || '-' }}
                </a-typography-text>
            </template>
            <template #provider_used="{ record }">
                <a-space>
                    <a-tag>{{ record.provider_used || '-' }}</a-tag>
                    <a-tag v-if="record.failover_triggered" color="orange" size="small">已转移</a-tag>
                </a-space>
            </template>
            <template #created_at="{ record }">
                {{ formatTime(record.created_at) }}
            </template>
            <template #actions="{ record }">
                <a-button size="small" @click="openDetail(record)">查看</a-button>
            </template>
        </a-table>

        <!-- 详情抽屉 -->
        <a-drawer
            :visible="detailVisible"
            title="调用详情"
            :width="640"
            @cancel="detailVisible = false"
            :footer="false"
        >
            <a-descriptions v-if="current" :column="1" bordered size="small">
                <a-descriptions-item label="调用ID">{{ current.call_id }}</a-descriptions-item>
                <a-descriptions-item label="调用用户">{{ current.root_user_name || '-' }}</a-descriptions-item>
                <a-descriptions-item label="Agent">{{ current.agent_id || '-' }}</a-descriptions-item>
                <a-descriptions-item label="类型">{{ current.call_type }}</a-descriptions-item>
                <a-descriptions-item label="Provider">
                    {{ current.provider_used }}
                    <a-tag v-if="current.failover_triggered" color="orange" size="small">已故障转移</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="IP">{{ current.ip_address || '-' }}</a-descriptions-item>
                <a-descriptions-item label="Token 用量">{{ current.tokens_used ?? '-' }}</a-descriptions-item>
                <a-descriptions-item label="时间">{{ formatTime(current.created_at) }}</a-descriptions-item>
                <a-descriptions-item label="输入">
                    <pre>{{ current.prompt || '(空)' }}</pre>
                </a-descriptions-item>
                <a-descriptions-item label="响应">
                    <pre>{{ current.response || '(空)' }}</pre>
                </a-descriptions-item>
            </a-descriptions>
        </a-drawer>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconSearch, IconRefresh } from '@arco-design/web-vue/es/icon'
import { aiApi } from '@/api/modules/ai'
import type { AICallLog, AIAuditSummary } from '@/types/ai'

const columns = [
    { title: 'ID', dataIndex: 'id', width: 60 },
    { title: '调用用户', slotName: 'root_user_name', width: 110 },
    { title: 'Agent', slotName: 'agent_id', width: 110 },
    { title: '类型', slotName: 'call_type', width: 140 },
    { title: '输入', slotName: 'prompt', ellipsis: true },
    { title: 'Provider', slotName: 'provider_used', width: 150 },
    { title: '时间', slotName: 'created_at', width: 160 },
    { title: '操作', slotName: 'actions', width: 80 },
]

const loading = ref(false)
const tableData = ref<AICallLog[]>([])
const summary = ref<AIAuditSummary | null>(null)
const currentPage = ref(1)
const filter = reactive({
    call_type: '',
    agent_id: '',
    dateRange: [] as string[],
})

const pagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0,
    showTotal: true,
})

const detailVisible = ref(false)
const current = ref<AICallLog | null>(null)

async function fetchData() {
    loading.value = true
    try {
        const params: any = {
            page: currentPage.value,
            call_type: filter.call_type || undefined,
            agent_id: filter.agent_id || undefined,
        }
        if (filter.dateRange?.length === 2) {
            params.start_date = filter.dateRange[0]
            params.end_date = filter.dateRange[1]
        }
        const res = await aiApi.listAuditLogs(params)
        tableData.value = res.data
        pagination.total = res.pagination.total
        pagination.current = res.pagination.page
    } catch (e: any) {
        Message.error(e.message || '加载失败')
    } finally {
        loading.value = false
    }
}

async function fetchSummary() {
    try {
        const res = await aiApi.getAuditSummary()
        summary.value = res.data
    } catch {
        /* ignore */
    }
}

function handleSearch() {
    currentPage.value = 1
    fetchData()
}

function resetFilter() {
    filter.call_type = ''
    filter.agent_id = ''
    filter.dateRange = []
    currentPage.value = 1
    fetchData()
}

function handlePageChange(page: number) {
    currentPage.value = page
    fetchData()
}

function openDetail(record: AICallLog) {
    current.value = record
    detailVisible.value = true
}

function formatTime(iso: string): string {
    if (!iso) return '-'
    const d = new Date(iso)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

onMounted(() => {
    fetchData()
    fetchSummary()
})
</script>

<style scoped>
.audit-page {
    padding: 4px;
}
.summary-row {
    margin-bottom: 16px;
}
.stat-card {
    text-align: center;
}
.stat-value {
    font-size: 28px;
    font-weight: 600;
    color: rgb(var(--primary-6));
}
.stat-value.warn { color: rgb(var(--warning-6)); }
.stat-value.ok { color: rgb(var(--success-6)); }
.stat-value.danger { color: rgb(var(--danger-6)); }
.stat-title {
    font-size: 13px;
    color: var(--color-text-3);
    margin-top: 4px;
}
.type-list {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    justify-content: center;
}
.toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
.text-muted {
    color: var(--color-text-3);
}
pre {
    background: var(--color-fill-2);
    padding: 8px;
    border-radius: 4px;
    font-size: 12px;
    max-height: 200px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
}
</style>
