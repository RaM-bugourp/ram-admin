<template>
  <div class="audit-view">
    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-row">
      <a-col :span="6">
        <a-card>
          <a-statistic title="总日志数" :value="stats.total" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日操作" :value="stats.today" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic title="今日登录" :value="stats.today_login" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="操作类型"
            :value="Object.keys(stats.by_action).length"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 过滤栏 -->
    <a-card class="filter-card">
      <a-row :gutter="16" align="center">
        <a-col :span="4">
          <a-select
            v-model="filters.action"
            placeholder="操作类型"
            allow-clear
            :options="actionOptions"
          />
        </a-col>
        <a-col :span="4">
          <a-select
            v-model="filters.resource"
            placeholder="资源类型"
            allow-clear
            :options="resourceOptions"
          />
        </a-col>
        <a-col :span="4">
          <a-input
            v-model="filters.username"
            placeholder="用户名搜索"
            allow-clear
          />
        </a-col>
        <a-col :span="5">
          <a-range-picker
            v-model="dateRange"
            style="width: 100%"
            format="YYYY-MM-DD"
          />
        </a-col>
        <a-col :span="3">
          <a-button type="primary" @click="fetchLogs">查询</a-button>
        </a-col>
        <a-col :span="4" style="text-align: right">
          <a-button
            status="danger"
            @click="handleCleanup"
            :disabled="!store.getters['user/isRoot']"
          >
            清理日志
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- 日志表格 -->
    <a-card>
      <a-table
        :data="logs"
        :pagination="{
          current: pagination.page,
          pageSize: pagination.page_size,
          total: pagination.total,
          showTotal: true,
        }"
        :loading="loading"
        row-key="id"
        @page-change="onPageChange"
      >
        <template #columns>
          <a-table-column title="时间" data-index="created_at" :width="170">
            <template #cell="{ record }">
              {{ formatTime(record.created_at) }}
            </template>
          </a-table-column>
          <a-table-column title="用户" data-index="username" :width="120" />
          <a-table-column title="操作" data-index="action_label" :width="100">
            <template #cell="{ record }">
              <a-tag :color="actionColor(record.action)">
                {{ record.action_label }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="资源" data-index="resource_label" :width="100">
            <template #cell="{ record }">
              <a-tag>{{ record.resource_label }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="资源ID" data-index="resource_id" :width="80" />
          <a-table-column title="详情" data-index="detail" ellipsis />
          <a-table-column title="IP" data-index="ip_address" :width="130" />
          <a-table-column title="User-Agent" data-index="user_agent" :width="200" ellipsis />
        </template>
      </a-table>
    </a-card>

    <!-- 清理对话框 -->
    <a-modal
      v-model:visible="cleanupVisible"
      title="清理过期日志"
      @ok="doCleanup"
      :ok-loading="cleanupLoading"
    >
      <a-form :model="cleanupForm" layout="vertical">
        <a-form-item label="保留天数" field="days">
          <a-input-number
            v-model="cleanupForm.days"
            :min="7"
            :max="365"
            :step="30"
          />
        </a-form-item>
      </a-form>
      <a-typography-text type="warning">
        ⚠ 此操作将永久删除超过保留天数的日志，不可恢复！
      </a-typography-text>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import store from '@/stores'
import {
  getAuditLogs,
  getAuditStats,
  cleanupAuditLogs,
  getActionOptions,
  getResourceOptions,
  type AuditLogItem,
  type AuditStats,
} from '@/api/modules/audit'

// ── 状态 ──
const loading = ref(false)
const logs = ref<AuditLogItem[]>([])
const stats = reactive<AuditStats>({
  total: 0,
  by_action: {},
  by_resource: {},
  today: 0,
  today_login: 0,
})
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
})
const actionOptions = ref<{ value: string; label: string }[]>([])
const resourceOptions = ref<{ value: string; label: string }[]>([])

const filters = reactive({
  action: '',
  resource: '',
  username: '',
})
const dateRange = ref<string[]>([])

const cleanupVisible = ref(false)
const cleanupLoading = ref(false)
const cleanupForm = reactive({ days: 90 })

// ── 颜色映射 ──
const actionColorMap: Record<string, string> = {
  LOGIN: 'green',
  LOGOUT: 'gray',
  LOGIN_FAIL: 'red',
  CREATE: 'arcoblue',
  UPDATE: 'orange',
  DELETE: 'red',
  EXPORT: 'cyan',
  APPROVE: 'green',
  REJECT: 'orangered',
  PASSWORD_RESET: 'purple',
  ASSIGN_ROLE: 'gold',
  OTHER: 'gray',
}
function actionColor(action: string): string {
  return actionColorMap[action] || 'gray'
}

function formatTime(ts: string): string {
  if (!ts) return ''
  const d = new Date(ts)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

// ── 数据加载 ──
async function fetchStats() {
  try {
    const res = await getAuditStats()
    Object.assign(stats, res.data)
  } catch {
    // stats not critical
  }
}

async function fetchLogs() {
  loading.value = true
  try {
    const params: Record<string, unknown> = {
      page: pagination.page,
      page_size: pagination.page_size,
    }
    if (filters.action) params.action = filters.action
    if (filters.resource) params.resource = filters.resource
    if (filters.username) params.username = filters.username
    if (dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const res = await getAuditLogs(params as any)
    logs.value = res.data
    pagination.total = res.pagination.total
  } catch (e: any) {
    Message.error('加载审计日志失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

async function fetchOptions() {
  try {
    const [actRes, resRes] = await Promise.all([
      getActionOptions(),
      getResourceOptions(),
    ])
    actionOptions.value = actRes.data
    resourceOptions.value = resRes.data
  } catch {
    // options not critical
  }
}

function onPageChange(page: number) {
  pagination.page = page
  fetchLogs()
}

function handleCleanup() {
  cleanupVisible.value = true
}

async function doCleanup() {
  cleanupLoading.value = true
  try {
    const res = await cleanupAuditLogs(cleanupForm.days)
    Message.success(`已清理 ${res.data.deleted} 条过期日志`)
    cleanupVisible.value = false
    fetchStats()
    fetchLogs()
  } catch (e: any) {
    Message.error('清理失败: ' + (e.message || '未知错误'))
  } finally {
    cleanupLoading.value = false
  }
}

onMounted(() => {
  fetchStats()
  fetchLogs()
  fetchOptions()
})
</script>

<style scoped>
.audit-view {
  padding: 0;
}
.stats-row {
  margin-bottom: 16px;
}
.filter-card {
  margin-bottom: 16px;
}
</style>