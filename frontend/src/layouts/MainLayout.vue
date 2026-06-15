<template>
    <a-layout class="main-layout">
        <a-layout-sider collapsible breakpoint="lg" :width="240">
            <div class="logo">AdminX</div>
            <a-menu
                :selected-keys="[currentPath]"
                @menu-item-click="navigate"
            >
                <a-menu-item key="/dashboard">
                    <template #icon><icon-apps /></template>
                    仪表盘
                </a-menu-item>
                <a-menu-item key="/system/users">
                    <template #icon><icon-user-group /></template>
                    用户管理
                </a-menu-item>
                <a-menu-item key="/system/roles">
                    <template #icon><icon-safe /></template>
                    角色管理
                </a-menu-item>
                <template v-if="isRoot">
                    <a-menu-item-group title="AI 智能">
                        <a-menu-item key="/ai/chat">
                            <template #icon><icon-robot /></template>
                            AI 对话
                        </a-menu-item>
                        <a-menu-item key="/ai/approval">
                            <template #icon><icon-check-square /></template>
                            Agent 审批
                            <a-badge v-if="pendingBadge" :count="pendingBadge" :offset="[6, -4]" />
                        </a-menu-item>
                        <a-menu-item key="/ai/audit">
                            <template #icon><icon-history /></template>
                            AI 审计
                        </a-menu-item>
                        <a-menu-item key="/ai/notifications">
                            <template #icon><icon-bell /></template>
                            AI 通知
                            <a-badge v-if="unreadCount" :count="unreadCount" :offset="[6, -4]" />
                        </a-menu-item>
                        <a-menu-item key="/ai/agent-token">
                            <template #icon><icon-lock /></template>
                            Agent Token
                        </a-menu-item>
                    </a-menu-item-group>
                </template>
            </a-menu>
        </a-layout-sider>
        <a-layout>
            <a-layout-header class="header">
                <a-space>
                    <span class="role-tag" v-if="isAdmin">
                        <a-tag :color="isRoot ? 'arcoblue' : 'red'" size="small">
                            {{ isRoot ? 'root' : 'BOSS' }}
                        </a-tag>
                    </span>
                    <span>{{ username }}</span>
                    <a-button type="text" @click="handleLogout">退出</a-button>
                </a-space>
            </a-layout-header>
            <a-layout-content class="content">
                <AIProviderAlert v-if="isRoot" />
                <router-view />
            </a-layout-content>
        </a-layout>
    </a-layout>
</template>

<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import {
    IconApps, IconUserGroup, IconSafe,
    IconRobot, IconCheckSquare, IconHistory, IconBell, IconLock,
} from '@arco-design/web-vue/es/icon'
import AIProviderAlert from '@/components/AIProviderAlert.vue'
import { aiApi } from '@/api/modules/ai'

const router = useRouter()
const route = useRoute()
const store = useStore()

const currentPath = computed(() => route.path)
const username = computed(() => store.state.user?.currentUser?.username || '')
const isRoot = computed(() => store.getters['user/isRoot'])
const isAdmin = computed(() => store.getters['user/isAdmin'])
const unreadCount = computed(() => store.state.ai.unreadNotifications || 0)

// 待审批数 — 仅 root 显示，进入布局后拉一次
const pendingBadge = ref(0)
import { ref } from 'vue'

async function loadPending() {
    if (!isRoot.value) return
    try {
        const res: any = await aiApi.listApprovals({ status: 'pending', page_size: 1 })
        pendingBadge.value = res.pagination?.total || 0
    } catch {
        /* ignore */
    }
}

function navigate(key: string) {
    router.push(key)
}

async function handleLogout() {
    await store.dispatch('user/logout')
    router.push('/login')
}

onMounted(() => {
    if (isRoot.value) {
        store.dispatch('ai/fetchProviderStatus')
        store.dispatch('ai/fetchUnreadCount')
        loadPending()
    }
})

// 登录态变化时重新拉取
watch(isRoot, (v) => {
    if (v) {
        store.dispatch('ai/fetchProviderStatus')
        store.dispatch('ai/fetchUnreadCount')
        loadPending()
    }
})
</script>

<style scoped>
.main-layout {
    height: 100vh;
}
.logo {
    height: 60px;
    line-height: 60px;
    text-align: center;
    font-size: 20px;
    font-weight: 700;
    color: var(--color-text-1);
    border-bottom: 1px solid var(--color-border-2);
}
.header {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    padding: 0 24px;
    background: var(--color-bg-2);
    border-bottom: 1px solid var(--color-border-2);
}
.content {
    padding: 16px 24px 24px;
    background: var(--color-fill-2);
    overflow-y: auto;
}
.role-tag {
    display: inline-flex;
    align-items: center;
}
</style>
