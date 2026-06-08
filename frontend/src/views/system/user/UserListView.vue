<template>
    <div class="user-page">
        <!-- 搜索栏 -->
        <div class="toolbar">
            <a-input-search
                v-model="searchText"
                placeholder="搜索用户名 / 邮箱"
                style="width: 320px"
                @search="handleSearch"
                allow-clear
            />
            <a-button type="primary" @click="handleCreate">
                <template #icon><icon-plus /></template>
                新建用户
            </a-button>
        </div>

        <!-- 表格 -->
        <a-table
            :columns="columns"
            :data="tableData"
            :loading="loading"
            :pagination="pagination"
            @page-change="handlePageChange"
            row-key="id"
        >
            <template #is_active="{ record }">
                <a-tag :color="record.is_active ? 'green' : 'red'">
                    {{ record.is_active ? '启用' : '禁用' }}
                </a-tag>
            </template>
            <template #is_superuser="{ record }">
                <a-tag v-if="record.is_superuser" color="arcoblue">超管</a-tag>
                <span v-else class="text-muted">-</span>
            </template>
            <template #created_at="{ record }">
                {{ formatTime(record.created_at) }}
            </template>
            <template #actions="{ record }">
                <a-space>
                    <a-button size="small" @click="handleEdit(record)">编辑</a-button>
                    <a-button size="small" status="warning" @click="handleResetPwd(record)">
                        重置密码
                    </a-button>
                    <a-popconfirm content="确定删除该用户？" @ok="handleDelete(record.id)">
                        <a-button size="small" status="danger">删除</a-button>
                    </a-popconfirm>
                </a-space>
            </template>
        </a-table>

        <!-- 新建 / 编辑弹窗 -->
        <UserFormDialog
            v-model:visible="dialogVisible"
            :user="editingUser"
            @success="fetchList"
        />

        <!-- 重置密码弹窗 -->
        <a-modal v-model:visible="pwdVisible" title="重置密码" @ok="confirmResetPwd" @cancel="pwdVisible = false">
            <a-form :model="pwdForm">
                <a-form-item label="新密码">
                    <a-input-password v-model="pwdForm.password" placeholder="至少6位" />
                </a-form-item>
            </a-form>
        </a-modal>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconPlus } from '@arco-design/web-vue/es/icon'
import { userApi } from '@/api/modules/user'
import type { UserOutput } from '@/types/user'
import UserFormDialog from './UserFormDialog.vue'

// ── 表格列定义 ──────────────────────────────────
const columns = [
    { title: 'ID', dataIndex: 'id', width: 70 },
    { title: '用户名', dataIndex: 'username', width: 150 },
    { title: '邮箱', dataIndex: 'email', ellipsis: true },
    { title: '状态', slotName: 'is_active', width: 80 },
    { title: '角色', slotName: 'is_superuser', width: 80 },
    { title: '创建时间', slotName: 'created_at', width: 170 },
    { title: '操作', slotName: 'actions', width: 230, fixed: 'right' as const },
]

// ── 数据状态 ────────────────────────────────────
const loading = ref(false)
const searchText = ref('')
const tableData = ref<UserOutput[]>([])
const currentPage = ref(1)
const total = ref(0)

const pagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0,
    showTotal: true,
})

// ── 弹窗状态 ────────────────────────────────────
const dialogVisible = ref(false)
const editingUser = ref<UserOutput | null>(null)
const pwdVisible = ref(false)
const resetPwdUserId = ref(0)
const pwdForm = reactive({ password: '' })

// ── 数据加载 ────────────────────────────────────
async function fetchList() {
    loading.value = true
    try {
        const res = await userApi.list({ page: currentPage.value, search: searchText.value })
        tableData.value = res.data
        total.value = res.pagination.total
        pagination.total = res.pagination.total
        pagination.current = res.pagination.page
    } catch (e: any) {
        Message.error(e.message || '加载失败')
    } finally {
        loading.value = false
    }
}

function handleSearch() {
    currentPage.value = 1
    fetchList()
}

function handlePageChange(page: number) {
    currentPage.value = page
    fetchList()
}

// ── CRUD 操作 ──────────────────────────────────
function handleCreate() {
    editingUser.value = null
    dialogVisible.value = true
}

function handleEdit(user: UserOutput) {
    editingUser.value = user
    dialogVisible.value = true
}

async function handleDelete(id: number) {
    try {
        await userApi.delete(id)
        Message.success('删除成功')
        fetchList()
    } catch (e: any) {
        Message.error(e.message || '删除失败')
    }
}

// ── 重置密码 ────────────────────────────────────
function handleResetPwd(user: UserOutput) {
    resetPwdUserId.value = user.id
    pwdForm.password = ''
    pwdVisible.value = true
}

async function confirmResetPwd() {
    if (pwdForm.password.length < 6) {
        Message.warning('密码至少6位')
        return
    }
    try {
        await userApi.resetPassword(resetPwdUserId.value, { password: pwdForm.password })
        Message.success('密码重置成功')
        pwdVisible.value = false
    } catch (e: any) {
        Message.error(e.message || '重置失败')
    }
}

// ── 工具函数 ────────────────────────────────────
function formatTime(iso: string): string {
    if (!iso) return '-'
    const d = new Date(iso)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(fetchList)
</script>

<style scoped>
.user-page {
    padding: 20px;
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
</style>
