<template>
  <div class="dashboard">
    <h2 class="page-title">欢迎使用 RaM Admin</h2>
    <p class="page-desc">企业级后台管理框架 · Django 5 + Vue 3 + Arco Design</p>

    <a-grid :cols="3" :col-gap="16" :row-gap="16" class="stat-grid">
      <a-grid-item v-for="stat in stats" :key="stat.key">
        <a-card class="stat-card">
          <div class="stat-icon" :style="{ background: stat.color }">
            <component :is="stat.icon" />
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </a-card>
      </a-grid-item>
    </a-grid>

    <a-card title="框架特性" class="features-card">
      <a-row :gutter="[24, 16]">
        <a-col :span="8" v-for="f in features" :key="f.title">
          <div class="feature-item">
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </a-col>
      </a-row>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getArticleStatistics } from '@/api/article'

const stats = ref([
  { key: 'articles', label: '文章', value: '-', color: '#e6f7ff', icon: 'icon-book' },
  { key: 'users', label: '用户', value: '-', color: '#f6ffed', icon: 'icon-user' },
  { key: 'menus', label: '菜单', value: '-', color: '#fff7e6', icon: 'icon-menu' },
])

const features = [
  { title: 'Mixin 叠加', desc: '审计字段、软删除、动作序列化器任意组合' },
  { title: 'RBAC 双模式', desc: 'URL 匹配 + 权限码两种权限控制' },
  { title: '数据权限', desc: '组织级数据隔离，按角色自动过滤' },
  { title: '操作日志', desc: '全局中间件，无侵入记录所有操作' },
  { title: '动态路由', desc: '后端菜单树驱动前端路由注册' },
  { title: '前后端分离', desc: 'Django DRF + Vue 3，分层清晰' },
]

onMounted(async () => {
  try {
    const res = await getArticleStatistics()
    if (res) {
      stats.value[0].value = res.total ?? '-'
      stats.value[1].value = '-'
      stats.value[2].value = '-'
    }
  } catch (e) {
    // ignore
  }
})
</script>

<style scoped>
.dashboard {
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.page-desc {
  color: #86909c;
  margin-bottom: 24px;
}

.stat-grid {
  margin-bottom: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1d2129;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #86909c;
  margin-top: 4px;
}

.features-card {
  margin-top: 16px;
}

.feature-item {
  padding: 12px;
  border-radius: 8px;
  background: #f7f8fa;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  margin-bottom: 4px;
}

.feature-desc {
  font-size: 12px;
  color: #86909c;
  line-height: 1.5;
}
</style>
