<template>
  <aside class="sidebar" :class="{ collapsed }">
    <!-- 折叠按钮 -->
    <div class="collapse-btn" @click="collapsed = !collapsed">
      <icon-menu-fold v-if="!collapsed" />
      <icon-menu-unfold v-else />
    </div>

    <!-- 菜单列表 -->
    <a-menu
      mode="vertical"
      :selected-keys="activeKeys"
      :collapsed="collapsed"
      @menu-item-click="handleMenuClick"
    >
      <template v-for="item in visibleMenu" :key="item.id || item.path">
        <!-- 有子菜单 -->
        <a-sub-menu v-if="item.children?.length" :key="item.id">
          <template #title>
            <component :is="getIcon(item.icon)" v-if="item.icon" />
            <span>{{ item.title }}</span>
          </template>
          <a-menu-item
            v-for="child in item.children.filter(c => !c.isHidden)"
            :key="child.id || child.path"
          >
            {{ child.title }}
          </a-menu-item>
        </a-sub-menu>

        <!-- 叶子菜单 -->
        <a-menu-item v-else :key="item.id || item.path">
          <component :is="getIcon(item.icon)" v-if="item.icon" />
          <span>{{ item.title }}</span>
        </a-menu-item>
      </template>
    </a-menu>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRoute, useRouter } from 'vue-router'

const store = useStore()
const route = useRoute()
const router = useRouter()

const collapsed = ref(false)

// 从 Vuex 读取菜单树
const menuTree = computed(() => store.state.menu.menuTree || [])

// 过滤隐藏菜单
const visibleMenu = computed(() => menuTree.value.filter(m => !m.isHidden))

// 高亮的菜单 key（根据当前路由匹配）
const activeKeys = computed(() => {
  const keys = []
  // 遍历菜单树找匹配的节点
  const find = (items) => {
    for (const item of items) {
      if (route.path.startsWith(item.path) && item.path !== '/') {
        keys.push(item.id || item.path)
      }
      if (item.children) find(item.children)
    }
  }
  find(menuTree.value)
  return keys
})

const handleMenuClick = (key) => {
  // 找到对应菜单的完整路径
  const findPath = (items, targetId) => {
    for (const item of items) {
      if ((item.id || item.path) === targetId) {
        return item.path
      }
      if (item.children) {
        const found = findPath(item.children, targetId)
        if (found) return found
      }
    }
    return null
  }
  const path = findPath(menuTree.value, key)
  if (path) {
    router.push(path)
  }
}

// 图标映射（Arco Design 图标）
const iconMap = {}
const getIcon = (iconName) => {
  // 动态导入图标组件
  return iconMap[iconName] || 'icon-app'
}
</script>

<style scoped>
.sidebar {
  width: 220px;
  min-width: 220px;
  height: calc(100vh - 50px);
  background: #fff;
  border-right: 1px solid #e5e6e8;
  overflow-y: auto;
  transition: width 0.2s, min-width 0.2s;
  position: sticky;
  top: 50px;
}

.sidebar.collapsed {
  width: 48px;
  min-width: 48px;
}

.collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #4e5969;
  font-size: 16px;
  border-bottom: 1px solid #e5e6e8;
}

.collapse-btn:hover {
  background: #f2f3f5;
}
</style>
