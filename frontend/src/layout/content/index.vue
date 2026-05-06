<template>
  <a-layout class="main-layout">
    <!-- 侧边栏 -->
    <a-layout-sider
      :collapsed="collapsed"
      :width="220"
      :collapsed-width="48"
      class="sider"
    >
      <div class="logo">
        <span v-if="!collapsed" class="logo-text">RaM Admin</span>
        <span v-else class="logo-icon">R</span>
      </div>
      <a-menu
        :selected-keys="selectedKeys"
        :open-keys="openKeys"
        :collapsed="collapsed"
        @menu-item-click="handleMenuClick"
        auto-open-selected
      >
        <template v-for="menu in sidebarMenus" :key="menu.id || menu.path">
          <SidebarItem :menu="menu" />
        </template>
      </a-menu>
    </a-layout-sider>

    <!-- 右侧内容区 -->
    <a-layout class="content-layout">
      <!-- 顶栏 -->
      <a-layout-header class="header">
        <div class="header-left">
          <a-button
            type="text"
            @click="collapsed = !collapsed"
          >
            <icon-menu-fold v-if="!collapsed" />
            <icon-menu-unfold v-else />
          </a-button>
          <a-breadcrumb>
            <a-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </a-breadcrumb-item>
          </a-breadcrumb>
        </div>
        <div class="header-right">
          <a-dropdown>
            <a-button type="text">
              <icon-user />
              <span class="username">{{ userInfo?.username || '用户' }}</span>
            </a-button>
            <template #content>
              <a-doption @click="handleLogout">
                <icon-export /> 退出登录
              </a-doption>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <!-- 主内容 -->
      <a-layout-content class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { Message } from '@arco-design/web-vue'

// 递归菜单项组件
const SidebarItem = {
  props: { menu: Object },
  setup(props) {
    const router = useRouter()
    
    if (props.menu.children?.length) {
      // 有子菜单
      return () => h(
        'a-sub-menu',
        { key: props.menu.id || props.menu.path },
        {
          title: () => [
            props.menu.icon && h(`icon-${props.menu.icon}`),
            h('span', props.menu.title),
          ],
          default: () =>
            props.menu.children.map((child) =>
              h(SidebarItem, { menu: child, key: child.id || child.path })
            ),
        }
      )
    } else {
      // 叶子菜单
      return () =>
        h(
          'a-menu-item',
          { key: props.menu.path },
          [
            props.menu.icon && h(`icon-${props.menu.icon}`),
            props.menu.title,
          ]
        )
    }
  },
}

const router = useRouter()
const route = useRoute()
const store = useStore()

const collapsed = ref(false)
const selectedKeys = ref([])
const openKeys = ref([])

// 用户信息
const userInfo = computed(() => store.state.user)
const sidebarMenus = computed(() => store.getters['menu/sidebarMenu'])

// 面包屑
const breadcrumbs = computed(() => {
  const matched = route.matched.filter((r) => r.meta?.title)
  return matched.map((r) => ({
    path: r.path,
    title: r.meta.title,
  }))
})

// 监听路由变化，更新选中菜单
watch(
  () => route.path,
  (path) => {
    selectedKeys.value = [path]
    // 自动展开父菜单
    const parts = path.split('/').filter(Boolean)
    const opens = []
    for (let i = 1; i < parts.length; i++) {
      opens.push('/' + parts.slice(0, i).join('/'))
    }
    openKeys.value = opens
  },
  { immediate: true }
)

// 菜单点击
const handleMenuClick = (key) => {
  router.push(key)
}

// 退出登录
const handleLogout = async () => {
  try {
    await store.dispatch('user/logout')
    Message.success('已退出登录')
    router.push('/login')
  } catch (e) {
    // ignore
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sider {
  background: #fff;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #f0f0f0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  color: #165dff;
}

.logo-icon {
  font-size: 24px;
  font-weight: 700;
  color: #165dff;
}

.content-layout {
  background: #f7f8fa;
}

.header {
  background: #fff;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
}

.username {
  margin-left: 4px;
}

.content {
  margin: 16px;
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  min-height: calc(100vh - 64px - 32px);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
