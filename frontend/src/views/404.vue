<template>
  <div class="not-found">
    <div class="content">
      <h1 class="code">404</h1>
      <h2 class="title">页面不存在</h2>
      <p class="desc">抱歉，您访问的页面不存在或已被移除。</p>
      <a-button type="primary" @click="$router.push('/')">
        返回首页
      </a-button>
    </div>
  </div>
</template>

<script setup></script>

<style scoped>
.not-found {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f2f5;
}

.code {
  font-size: 120px;
  font-weight: 700;
  color: #165dff;
  line-height: 1;
}

.title {
  font-size: 24px;
  color: #1d2129;
  margin: 16px 0 8px;
}

.desc {
  color: #86909c;
  margin-bottom: 24px;
}
</style>
