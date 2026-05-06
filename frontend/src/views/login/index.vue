<template>
  <div class="login-page">
    <div class="login-card">
      <h1 class="title">RaM Admin</h1>
      <p class="subtitle">企业级后台管理框架</p>

      <a-form
        :model="form"
        @submit="handleLogin"
        layout="vertical"
        class="login-form"
      >
        <a-form-item
          label="用户名"
          :validate-status="errors.username ? 'error' : ''"
          :help="errors.username"
        >
          <a-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix><icon-user /></template>
          </a-input>
        </a-form-item>

        <a-form-item
          label="密码"
          :validate-status="errors.password ? 'error' : ''"
          :help="errors.password"
        >
          <a-input-password
            v-model="form.password"
            placeholder="请输入密码"
            size="large"
            @keyup.enter="handleLogin"
          >
            <template #prefix><icon-lock /></template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            long
            size="large"
          >
            登 录
          </a-button>
        </a-form-item>
      </a-form>

      <div class="hint">
        默认账号：admin / admin123
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Message } from '@arco-design/web-vue'

const router = useRouter()
const store = useStore()

const form = ref({ username: '', password: '' })
const errors = ref({})
const loading = ref(false)

const handleLogin = async () => {
  errors.value = {}
  if (!form.value.username) {
    errors.value.username = '请输入用户名'
    return
  }
  if (!form.value.password) {
    errors.value.password = '请输入密码'
    return
  }

  loading.value = true
  try {
    const ok = await store.dispatch('user/login', {
      username: form.value.username,
      password: form.value.password,
    })
    if (ok) {
      Message.success('登录成功')
      router.push('/')
    }
  } catch (e) {
    // axios interceptor 已经处理了错误提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 400px;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.title {
  text-align: center;
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  margin-bottom: 4px;
}

.subtitle {
  text-align: center;
  color: #86909c;
  font-size: 14px;
  margin-bottom: 32px;
}

.hint {
  text-align: center;
  font-size: 12px;
  color: #c9cdd4;
  margin-top: 8px;
}
</style>
