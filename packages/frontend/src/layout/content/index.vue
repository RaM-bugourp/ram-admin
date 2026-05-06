<template>
  <div class="layout-wrapper">
    <!-- 顶部导航栏 -->
    <Navbar />

    <div class="content-area">
      <!-- 左侧边栏 -->
      <SideBar />

      <!-- 主内容区 -->
      <main class="main-content">
        <!-- 路由视图：切换不同页面 -->
        <transition name="fade-transform" mode="out-in">
          <router-view :key="$route.path" />
        </transition>
      </main>
    </div>
  </div>
</template>

<script setup>
import Navbar from '@/layout/navbar'
import SideBar from '@/layout/sidebar'
</script>

<style scoped>
.layout-wrapper {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.content-area {
  display: flex;
  flex: 1;
  overflow: hidden;
  /* 减去 Navbar 的高度（50px） */
  margin-top: 50px;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  background: #f0f2f5;
  padding: 16px;
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: opacity 0.15s ease;
}
.fade-transform-enter-from,
.fade-transform-leave-to {
  opacity: 0;
}
</style>
