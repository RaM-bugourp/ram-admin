<template>
    <div class="role-page">
        <!-- 工具栏 -->
        <div class="toolbar">
            <a-button v-if="isAdmin" type="primary" @click="handleCreate">
                <template #icon><icon-plus /></template>
                新建角色
            </a-button>
            <span class="toolbar-hint">
                <icon-info-circle /> 系统角色 (root/user/boss) 编码不可修改、不可删除
            </span>
        </div>

        <!-- 表格 -->
        <a-table
            :columns="columns"
            :data="tableData"
            :loading="loading"
            row-key="id"
            :pagination="false"
        >
            <template #name="{ record }">
                <a-space>
                    <span>{{ record.name }}</span>
                    <a-tag v-if="record.is_unique" color="red" size="small">唯一</a-tag>
                    <a-tag v-if="isSystemRole(record.code)" color="arcoblue" size="small">系统</a-tag>
                </a-space>
            </template>
            <template #code="{ record }">
                <a-tag>{{ record.code }}</a-tag>
            </template>
            <template #description="{ record }">
                <span class="text-muted">{{ record.description || '-' }}</span>
            </template>
            <template #user_count="{ record }">
                <a-tag :color="record.user_count > 0 ? 'green' : 'gray'">
                    {{ record.user_count }} 人
                </a-tag>
            </template>
            <template #actions="{ record }">
                <a-space v-if="isAdmin">
                    <a-button size="small" @click="handleEdit(record)">编辑</a-button>
                    <a-popconfirm
                        content="确定删除该角色？持有该角色的用户将被自动解绑。"
                        @ok="handleDelete(record.id)"
                        :disabled="isSystemRole(record.code)"
                    >
                        <a-button
                            size="small"
                            status="danger"
                            :disabled="isSystemRole(record.code)"
                        >
                            删除
                        </a-button>
                    </a-popconfirm>
                </a-space>
                <span v-else class="text-muted">—</span>
            </template>
        </a-table>

        <!-- 新建/编辑弹窗 -->
        <RoleFormDialog
            v-model:visible="showDialog"
            :role="editingRole"
            @success="fetchRoles"
        />
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { Message } from '@arco-design/web-vue'
import { IconPlus, IconInfoCircle } from '@arco-design/web-vue/es/icon'
import { roleApi } from '@/api/modules/role'
import type { RoleOutput } from '@/types/role'
import RoleFormDialog from './RoleFormDialog.vue'

const store = useStore()
const isAdmin = computed(() => store.getters['user/isAdmin'])

const SYSTEM_ROLES = ['root', 'user', 'boss']

const loading = ref(false)
const tableData = ref<RoleOutput[]>([])
const showDialog = ref(false)
const editingRole = ref<RoleOutput | null>(null)

const columns = [
    { title: '角色名', slotName: 'name', width: 200 },
    { title: '编码', slotName: 'code', width: 120 },
    { title: '描述', slotName: 'description', ellipsis: true },
    { title: '成员数', slotName: 'user_count', width: 100, align: 'center' as const },
    { title: '操作', slotName: 'actions', width: 180 },
]

function isSystemRole(code: string): boolean {
    return SYSTEM_ROLES.includes(code)
}

async function fetchRoles() {
    loading.value = true
    try {
        const res = await roleApi.list()
        tableData.value = res.data
    } catch (e: any) {
        Message.error(e.message || '加载角色列表失败')
    } finally {
        loading.value = false
    }
}

function handleCreate() {
    editingRole.value = null
    showDialog.value = true
}

function handleEdit(role: RoleOutput) {
    editingRole.value = role
    showDialog.value = true
}

async function handleDelete(id: number) {
    try {
        await roleApi.delete(id)
        Message.success('角色已删除')
        fetchRoles()
    } catch (e: any) {
        Message.error(e.message || '删除失败')
    }
}

onMounted(fetchRoles)
</script>

<style scoped>
.role-page {
    padding: 0;
}
.toolbar {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 16px;
}
.toolbar-hint {
    font-size: 13px;
    color: var(--color-text-3);
    display: flex;
    align-items: center;
    gap: 4px;
}
.text-muted {
    color: var(--color-text-3);
}
</style>
