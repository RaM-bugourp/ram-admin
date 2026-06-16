<template>
    <div class="login-page">
        <a-card class="login-card" :bordered="false">
            <template #title>
                <div class="login-title">Django-Vue-AdminX</div>
            </template>
            <a-form :model="form" layout="vertical" @submit="handleLogin">
                <a-form-item field="username" label="用户名" :rules="[{ required: true, message: '请输入用户名' }]">
                    <a-input v-model="form.username" placeholder="admin" allow-clear />
                </a-form-item>
                <a-form-item field="password" label="密码" :rules="[{ required: true, message: '请输入密码' }]">
                    <a-input-password v-model="form.password" placeholder="admin123" allow-clear />
                </a-form-item>
                <a-form-item>
                    <a-button type="primary" html-type="submit" long :loading="loading">登录</a-button>
                </a-form-item>
                <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
            </a-form>
        </a-card>
    </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, isNavigationFailure } from 'vue-router'
import { useStore } from 'vuex'
import { Message } from '@arco-design/web-vue'
import client from '@/api/client'

const router = useRouter()
const store = useStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

// 首次加载时 GET Django 让它下发 csrftoken cookie，否则后续 POST 直接 403
onMounted(() => {
    client.get('/auth/csrf/').catch(() => {})
})

// Arco 的 @submit 传递 (values, ev)，显式 preventDefault 防止原生表单提
// 交导致页面刷新回 /login，从而丢失 SPA 中的登录态
async function handleLogin(_values: any, ev?: Event) {
    ev?.preventDefault()
    if (!form.username || !form.password) return
    loading.value = true
    errorMsg.value = ''
    try {
        await store.dispatch('user/login', {
            username: form.username,
            password: form.password,
        })
        Message.success('登录成功')
        // 用 replace 避免用户在仪表盘按回退回到登录页
        const failure = await router.replace('/')
        // 导航被拦截（如 guard 返回 false / 重定向）则提示
        if (isNavigationFailure(failure)) {
            errorMsg.value = '无法跳转，请检查账户权限'
        }
    } catch (e: any) {
        errorMsg.value = e.message || '登录失败'
    } finally {
        loading.value = false
    }
}
</script>

<style scoped>
.login-page {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: var(--color-fill-2);
}
.login-card {
    width: 400px;
}
.login-title {
    text-align: center;
    font-size: 22px;
    font-weight: 700;
}
.error-msg {
    color: rgb(var(--danger-6));
    text-align: center;
    font-size: 13px;
}
</style>
