<template>
    <div class="error-page">
        <h1>404</h1>
        <p>页面不存在</p>
        <a-button type="primary" @click="$router.push('/dashboard')">返回首页</a-button>
    </div>
</template>

<style scoped>
.error-page {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100vh;
    gap: 16px;
}
.error-page h1 {
    font-size: 72px;
    color: var(--color-text-3);
    margin: 0;
}
</style>
