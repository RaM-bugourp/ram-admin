<template><a-card title="个人设置">
 <a-alert v-if="error" type="error">{{error}} <a-button @click="load">重试</a-button></a-alert>
 <a-spin :loading="loading"><a-descriptions :column="1"><a-descriptions-item label="用户名">{{info.username}}</a-descriptions-item><a-descriptions-item label="邮箱">{{info.email}}</a-descriptions-item><a-descriptions-item label="AI 扩展">{{info.ai_enabled?'已显式启用（可选）':'未启用；核心后台不依赖 Provider'}}</a-descriptions-item></a-descriptions></a-spin>
 <a-divider/> <h3>修改本人密码</h3><a-form :model="form" layout="vertical" style="max-width:480px" @submit.prevent="save">
 <a-form-item label="原密码"><a-input-password v-model="form.old_password" autocomplete="current-password"/></a-form-item>
 <a-form-item label="新密码"><a-input-password v-model="form.new_password" autocomplete="new-password" placeholder="至少8位，不能过于简单"/></a-form-item>
 <a-button type="primary" :loading="saving" @click="save">修改密码</a-button><p>修改成功后保留当前会话，其他会话失效。</p></a-form>
 <a-divider/><h3>账户安全中心</h3><p>仅显示安全句柄和时间，不展示 Cookie、会话密钥、IP 或设备原始信息。退出其他会话保留当前会话。</p>
 <a-alert v-if="sessionError" type="error">{{sessionError}} <a-button @click="loadSessions">重试会话</a-button></a-alert>
 <a-space style="margin-bottom:12px"><a-button @click="loadSessions" :loading="sessionLoading">刷新会话</a-button><a-popconfirm content="退出本人的其他所有会话？当前会话保留。" @ok="revokeOthers"><a-button status="warning" :loading="revoking">退出其他会话</a-button></a-popconfirm></a-space>
 <a-table :data="sessions" :pagination="false" :loading="sessionLoading" row-key="id" :scroll="{x:700}"><template #columns><a-table-column title="会话句柄" data-index="id"/><a-table-column title="登记时间" data-index="created_at"/><a-table-column title="过期时间" data-index="expires_at"/><a-table-column title="状态"><template #cell="{record}">{{record.current?'当前会话':'其他会话'}}</template></a-table-column><a-table-column title="操作"><template #cell="{record}"><a-popconfirm v-if="!record.current" content="退出该会话？" @ok="revokeOne(record.id)"><a-button size="small" :disabled="revoking">退出会话</a-button></a-popconfirm></template></a-table-column></template></a-table>
</a-card></template>
<script setup lang="ts">
import {ref,reactive,onMounted} from 'vue'
import {Message} from '@arco-design/web-vue'
import client from '@/api/client'
const info=ref<any>({}),loading=ref(false),saving=ref(false),error=ref(''),form=reactive({old_password:'',new_password:''})
async function load(){loading.value=true;error.value='';try{const r:any=await client.get('/auth/settings/');info.value=r.data}catch(e:any){error.value=e.message}finally{loading.value=false}}
async function save(){if(saving.value)return;if(!form.old_password||form.new_password.length<8){Message.warning('请输入原密码和至少8位新密码');return}saving.value=true;try{await client.post('/auth/change-password/',form);form.old_password='';form.new_password='';Message.success('密码修改成功')}catch(e:any){Message.error(e.message)}finally{saving.value=false}}
const sessions=ref<any[]>([]),sessionLoading=ref(false),sessionError=ref(''),revoking=ref(false)
async function loadSessions(){sessionLoading.value=true;sessionError.value='';try{const r:any=await client.get('/auth/sessions/');sessions.value=r.data}catch(e:any){sessionError.value=e.message}finally{sessionLoading.value=false}}
async function revokeOthers(){if(revoking.value)return;revoking.value=true;try{await client.post('/auth/revoke-other-sessions/',{});Message.success('其他会话已退出');await loadSessions()}catch(e:any){sessionError.value=e.message}finally{revoking.value=false}}
async function revokeOne(id:string){if(revoking.value)return;revoking.value=true;try{await client.post('/auth/revoke-session/',{id});Message.success('会话已退出');await loadSessions()}catch(e:any){sessionError.value=e.message}finally{revoking.value=false}}
onMounted(()=>{load();loadSessions()})
</script>
