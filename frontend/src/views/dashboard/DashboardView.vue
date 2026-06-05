<template>
    <div class="dashboard">
        <h3>仪表盘</h3>
        <a-row :gutter="16" class="stats-row">
            <a-col :span="6" v-for="card in cards" :key="card.title">
                <a-card :bordered="false" class="stat-card">
                    <div class="stat-value">{{ card.value }}</div>
                    <div class="stat-title">{{ card.title }}</div>
                </a-card>
            </a-col>
        </a-row>
        <a-card :bordered="false" class="welcome-card">
            <p>欢迎使用 Django-Vue-AdminX 后台管理系统。</p>
            <p>这是一个最小可运行 Demo，后续将逐步添加用户管理、角色权限、菜单管理等功能。</p>
        </a-card>
    </div>
</template>

<script setup lang="ts">
const cards = [
    { title: '用户数', value: '—' },
    { title: '角色数', value: '—' },
    { title: '权限数', value: '—' },
    { title: '菜单数', value: '—' },
]
</script>

<style scoped>
.dashboard h3 {
    margin-bottom: 16px;
}
.stats-row {
    margin-bottom: 24px;
}
.stat-card {
    text-align: center;
}
.stat-value {
    font-size: 32px;
    font-weight: 600;
    color: rgb(var(--primary-6));
}
.stat-title {
    font-size: 14px;
    color: var(--color-text-3);
    margin-top: 8px;
}
.welcome-card p {
    margin: 8px 0;
    color: var(--color-text-2);
}
</style>
