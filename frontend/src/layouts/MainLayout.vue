<template>
 <a-layout class="main-layout">
  <a-layout-sider collapsible breakpoint="lg" :width="200"><div class="logo">AdminX</div>
   <a-menu :selected-keys="[route.path]" @menu-item-click="navigate">
    <a-menu-item key="/dashboard">工作台</a-menu-item>
    <a-menu-item v-if="can('users.read')" key="/system/users">用户管理</a-menu-item>
    <a-menu-item v-if="can('roles.read')" key="/system/roles">角色与权限</a-menu-item>
    <a-menu-item v-if="can('audit.read')" key="/system/audit">操作审计</a-menu-item>
    <a-menu-item key="/settings">个人设置</a-menu-item>
    <a-menu-item-group v-if="aiEnabled && isRoot" title="可选 AI 扩展">
     <a-menu-item key="/ai/chat">AI 对话</a-menu-item><a-menu-item key="/ai/approval">Agent 审批</a-menu-item><a-menu-item key="/ai/audit">AI 审计</a-menu-item><a-menu-item key="/ai/notifications">AI 通知</a-menu-item><a-menu-item key="/ai/agent-token">Agent Token</a-menu-item>
    </a-menu-item-group>
   </a-menu>
  </a-layout-sider>
  <a-layout class="body-layout"><a-layout-header class="header"><span>{{ username }}</span><a-tag v-if="isRoot">root</a-tag><a-button @click="handleLogout" :loading="leaving">退出</a-button></a-layout-header>
   <a-layout-content class="content"><AIProviderAlert v-if="aiEnabled && route.path.startsWith('/ai/')"/><router-view/></a-layout-content>
  </a-layout>
 </a-layout>
</template>
<script setup lang="ts">
import { computed,ref } from 'vue'
import { useRouter,useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { Message } from '@arco-design/web-vue'
import AIProviderAlert from '@/components/AIProviderAlert.vue'
const router=useRouter(),route=useRoute(),store=useStore(),leaving=ref(false)
const username=computed(()=>store.state.user.currentUser?.username||'')
const isRoot=computed(()=>store.getters['user/isRoot']),aiEnabled=computed(()=>store.state.user.aiEnabled)
const can=(code:string)=>store.getters['user/can'](code)
function navigate(key:string){router.push(key)}
async function handleLogout(){if(leaving.value)return;leaving.value=true;try{await store.dispatch('user/logout');router.replace('/login')}catch(e:any){Message.error(e.message||'退出失败，请重试')}finally{leaving.value=false}}
</script>
<style scoped>
.main-layout{height:100vh}.body-layout{min-width:0}.logo{padding:20px;text-align:center;font-weight:bold;font-size:20px}.header{display:flex;justify-content:flex-end;align-items:center;gap:12px;padding:12px 20px;background:var(--color-bg-2)}.content{padding:16px;overflow:auto;background:var(--color-fill-2);min-width:0}
</style>
