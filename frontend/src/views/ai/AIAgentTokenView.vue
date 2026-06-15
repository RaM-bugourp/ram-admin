<template>
    <div class="token-page">
        <a-card :bordered="false" title="签发 Agent 授权 Token">
            <p class="hint">
                root 可以为 Agent 签发授权 Token。Agent 凭借此 Token 可以提交审批请求（但所有写操作仍需 root 审批）。
                Token 仅在签发时返回一次，请妥善保存。
            </p>
            <a-form :model="form" layout="inline" @submit="handleIssue">
                <a-form-item field="agent_id" label="Agent ID" :rules="[{ required: true, message: '请输入 Agent ID' }]">
                    <a-input v-model="form.agent_id" placeholder="如 audit-bot" style="width: 220px" />
                </a-form-item>
                <a-form-item field="ttl_hours" label="有效期（小时）">
                    <a-input-number v-model="form.ttl_hours" :min="1" :max="720" style="width: 140px" />
                </a-form-item>
                <a-form-item>
                    <a-button type="primary" html-type="submit" :loading="loading">签发</a-button>
                </a-form-item>
            </a-form>
        </a-card>

        <a-card v-if="issuedToken" :bordered="false" title="签发结果" style="margin-top: 16px">
            <a-alert type="warning" title="请立即保存" style="margin-bottom: 12px">
                Token 仅在本次返回，刷新页面后将无法再次获取。
            </a-alert>
            <a-textarea
                :model-value="issuedToken"
                readonly
                :auto-size="{ minRows: 3, maxRows: 6 }"
            />
            <a-space style="margin-top: 12px">
                <a-button @click="copyToken">
                    <template #icon><icon-copy /></template>
                    复制
                </a-button>
                <a-button @click="issuedToken = ''">清除</a-button>
            </a-space>

            <a-divider />
            <h4>使用方式（curl 示例）</h4>
            <pre class="example">curl -X POST http://127.0.0.1:8000/api/ai/approval/submit/ \
  -H "Content-Type: application/json" \
  -H "X-Agent-Token: {{ issuedToken }}" \
  -d '{
    "agent_id": "{{ form.agent_id }}",
    "operation": "create_user",
    "params": {"username": "x", "email": "x@x.com", "password": "pass1234"},
    "reason": "Agent 测试"
  }'</pre>
        </a-card>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconCopy } from '@arco-design/web-vue/es/icon'
import { aiApi } from '@/api/modules/ai'

const loading = ref(false)
const issuedToken = ref('')
const form = reactive({
    agent_id: '',
    ttl_hours: 24,
})

async function handleIssue() {
    if (!form.agent_id) {
        Message.warning('请输入 Agent ID')
        return
    }
    loading.value = true
    try {
        const res = await aiApi.issueAgentToken({
            agent_id: form.agent_id,
            ttl_hours: form.ttl_hours,
        })
        issuedToken.value = res.data.token
        Message.success(`Token 已签发，有效期 ${res.data.expires_in_hours} 小时`)
    } catch (e: any) {
        Message.error(e.message || '签发失败')
    } finally {
        loading.value = false
    }
}

async function copyToken() {
    if (!issuedToken.value) return
    try {
        await navigator.clipboard.writeText(issuedToken.value)
        Message.success('已复制到剪贴板')
    } catch {
        Message.warning('复制失败，请手动选择复制')
    }
}
</script>

<style scoped>
.token-page {
    padding: 4px;
    max-width: 900px;
}
.hint {
    color: var(--color-text-2);
    font-size: 13px;
    margin-top: 0;
}
.example {
    background: var(--color-fill-3);
    color: var(--color-text-1);
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 12px;
    font-family: 'Consolas', monospace;
    white-space: pre;
}
</style>
