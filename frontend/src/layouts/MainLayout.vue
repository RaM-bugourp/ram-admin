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
            </a-menu>
        </a-layout-sider>
        <a-layout>
            <a-layout-header class="header">
                <a-space>
                    <span>{{ username }}</span>
                    <a-button type="text" @click="handleLogout">退出</a-button>
                </a-space>
            </a-layout-header>
            <a-layout-content class="content">
                <router-view />
            </a-layout-content>
        </a-layout>
    </a-layout>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { IconApps, IconUserGroup } from '@arco-design/web-vue/es/icon'

const router = useRouter()
const route = useRoute()
const store = useStore()

const currentPath = computed(() => route.path)
const username = computed(() => store.state.user?.currentUser?.username || '')

function navigate(key: string) {
    router.push(key)
}

async function handleLogout() {
    await store.dispatch('user/logout')
    router.push('/login')
}
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
    padding: 24px;
    background: var(--color-fill-2);
    overflow-y: auto;
}
</style>
