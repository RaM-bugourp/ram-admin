<template>
    <div class="notif-page">
        <div class="toolbar">
            <a-space>
                <a-radio-group v-model="onlyUnread" @change="fetchList" type="button">
                    <a-radio :value="false">全部</a-radio>
                    <a-radio :value="true">仅未读</a-radio>
                </a-radio-group>
            </a-space>
            <a-button @click="markAllRead" :disabled="!unreadCount">
                <template #icon><icon-check /></template>
                全部标记已读
            </a-button>
        </div>

        <a-list :loading="loading" :bordered="false">
            <a-list-item v-for="n in list" :key="n.id" :class="{ unread: !n.is_read }">
                <a-list-item-meta>
                    <template #title>
                        <a-space>
                            <a-tag :color="levelColor(n.level)" size="small">{{ levelLabel(n.level) }}</a-tag>
                            <span>{{ n.title }}</span>
                            <a-tag v-if="!n.is_read" color="orange" size="small">未读</a-tag>
                        </a-space>
                    </template>
                    <template #description>
                        <div class="msg-body">{{ n.message }}</div>
                        <div class="msg-time">{{ formatTime(n.created_at) }}</div>
                    </template>
                    <template #avatar>
                        <a-avatar :style="{ backgroundColor: avatarColor(n.level) }">
                            <icon-notification />
                        </a-avatar>
                    </template>
                </a-list-item-meta>
                <template #actions>
                    <a-button v-if="!n.is_read" size="small" @click="markRead(n.id)">标记已读</a-button>
                </template>
            </a-list-item>
            <a-list-item v-if="!list.length && !loading">
                <a-empty description="暂无通知" />
            </a-list-item>
        </a-list>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconCheck, IconNotification } from '@arco-design/web-vue/es/icon'
import { useStore } from 'vuex'
import { aiApi } from '@/api/modules/ai'
import type { AINotification, NotificationLevel } from '@/types/ai'

const store = useStore()
const loading = ref(false)
const list = ref<AINotification[]>([])
const onlyUnread = ref(false)
const unreadCount = ref(0)

const LEVEL_MAP: Record<NotificationLevel, { label: string; color: string; bg: string }> = {
    info: { label: '信息', color: 'arcoblue', bg: 'rgb(var(--primary-6))' },
    success: { label: '成功', color: 'green', bg: 'rgb(var(--success-6))' },
    warning: { label: '警告', color: 'orange', bg: 'rgb(var(--warning-6))' },
    error: { label: '错误', color: 'red', bg: 'rgb(var(--danger-6))' },
}

function levelLabel(l: NotificationLevel) { return LEVEL_MAP[l]?.label || l }
function levelColor(l: NotificationLevel) { return LEVEL_MAP[l]?.color || 'gray' }
function avatarColor(l: NotificationLevel) { return LEVEL_MAP[l]?.bg || 'gray' }

async function fetchList() {
    loading.value = true
    try {
        const res = await aiApi.listNotifications({ unread: onlyUnread.value || undefined })
        list.value = res.data
        unreadCount.value = res.unread_count
    } catch (e: any) {
        Message.error(e.message || '加载失败')
    } finally {
        loading.value = false
    }
}

async function markRead(id: number) {
    try {
        await aiApi.markNotificationRead(id)
        const item = list.value.find((n) => n.id === id)
        if (item) item.is_read = true
        store.dispatch('ai/fetchUnreadCount')
    } catch (e: any) {
        Message.error(e.message || '操作失败')
    }
}

async function markAllRead() {
    try {
        await aiApi.markAllNotificationsRead()
        Message.success('已全部标记为已读')
        fetchList()
        store.dispatch('ai/fetchUnreadCount')
    } catch (e: any) {
        Message.error(e.message || '操作失败')
    }
}

function formatTime(iso: string): string {
    if (!iso) return '-'
    const d = new Date(iso)
    const pad = (n: number) => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

onMounted(fetchList)
</script>

<style scoped>
.notif-page {
    padding: 4px;
    max-width: 900px;
}
.toolbar {
    display: flex;
    justify-content: space-between;
    margin-bottom: 16px;
}
.unread {
    background: var(--color-fill-1);
}
.msg-body {
    white-space: pre-wrap;
    color: var(--color-text-2);
}
.msg-time {
    font-size: 12px;
    color: var(--color-text-3);
    margin-top: 4px;
}
</style>
