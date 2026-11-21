<template><div><h2>工作台</h2><a-alert v-if="error" type="error">{{error}} <a-button @click="load">重试</a-button></a-alert><a-spin :loading="loading"><a-row :gutter="16"><a-col v-for="card in cards" :key="card.title" :xs="12" :lg="6"><a-card style="margin-bottom:16px"><h2>{{card.value ?? '无查看权限'}}</h2>{{card.title}}</a-card></a-col></a-row></a-spin><a-card title="后台管理"><p>数据来自当前有效用户、角色与角色关联，不包含演示活动或虚构图表。</p><p>按已授予权限使用左侧功能。个人密码和账户信息可在个人设置中管理。</p><a-button @click="router.push('/settings')">个人设置</a-button><p>AI 为可选扩展，核心管理不依赖任何 Provider。</p></a-card></div></template>
<script setup lang="ts">
import {ref,computed,onMounted} from 'vue'
import {useRouter} from 'vue-router'
import {dashboardApi} from '@/api/modules/dashboard'
const router=useRouter(),stats=ref<any>({}),loading=ref(false),error=ref('')
const cards=computed(()=>[{title:'用户总数',value:stats.value.total_users},{title:'活跃用户',value:stats.value.active_users},{title:'有效角色',value:stats.value.total_roles},{title:'有效角色关联',value:stats.value.total_assignments}])
async function load(){loading.value=true;error.value='';try{const r=await dashboardApi.getStats();stats.value=r.data}catch(e:any){error.value=e.message}finally{loading.value=false}}onMounted(load)
</script>
