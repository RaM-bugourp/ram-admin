<template>
  <header class="navbar">
    <!-- 左侧：Logo + 系统名 -->
    <div class="navbar-left">
      <span class="logo-text">RaM Admin</span>
    </div>

    <!-- 右侧：用户信息 -->
    <div class="navbar-right">
      <a-dropdown trigger="click" @select="handleMenuSelect">
        <div class="user-info">
          <a-avatar :size="32" class="avatar">
            {{ usernameFirstChar }}
          </a-avatar>
          <span class="username">{{ username }}</span>
          <icon-down />
        </div>
        <template #content>
          <a-doption value="profile">
            <template #icon><icon-user /></template>
            个人中心
          </a-doption>
          <a-doption value="logout" divided>
            <template #icon><icon-export /></template>
            退出登录
          </a-doption>
        </template>
      </a-dropdown>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Message } from '@arco-design/web-vue'

const store = useStore()
const router = useRouter()

const username = computed(() => store.state.user.username || 'Admin')
const usernameFirstChar = computed(() => username.value.charAt(0).toUpperCase())

const handleMenuSelect = async ({ value }) => {
  if (value === 'profile') {
    router.push('/profile')
  } else if (value === 'logout') {
    await store.dispatch('user/logout')
    Message.success('已退出登录')
    router.push('/login')
  }
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 50px;
  background: #fff;
  border-bottom: 1px solid #e5e6e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  z-index: 100;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.navbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: #1d2129;
  letter-spacing: 0.5px;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}

.user-info:hover {
  background: #f2f3f5;
}

.avatar {
  background: #165dff;
  color: #fff;
  font-weight: 600;
}

.username {
  font-size: 14px;
  color: #4e5969;
}
</style>
