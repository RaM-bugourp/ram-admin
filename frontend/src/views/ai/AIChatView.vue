<template>
    <div class="ai-chat-page">
        <div class="chat-header">
            <h3>
                AI 智能对话
                <a-tag v-if="isMockMode" color="orange" size="small">Mock 模式</a-tag>
                <a-tag v-else-if="providerStatus" color="arcoblue" size="small">
                    {{ providerStatus.current_provider }}
                </a-tag>
            </h3>
            <p class="hint">用自然语言提问，AI 会基于系统数据回答（仅 root 可用）。</p>
        </div>

        <a-row :gutter="16" class="chat-body">
            <!-- 左侧对话区 -->
            <a-col :span="18">
                <a-card :bordered="false" class="chat-card">
                    <div ref="msgBoxRef" class="message-list">
                        <div v-if="!messages.length" class="empty-tip">
                            <icon-robot :size="48" />
                            <p>开始和 AI 对话吧 👋</p>
                            <div class="suggest-list">
                                <a-button
                                    v-for="s in suggestions"
                                    :key="s"
                                    long
                                    @click="useSuggestion(s)"
                                >
                                    {{ s }}
                                </a-button>
                            </div>
                        </div>

                        <div
                            v-for="(msg, idx) in messages"
                            :key="idx"
                            class="message-row"
                            :class="msg.role"
                        >
                            <div class="avatar">
                                <icon-user v-if="msg.role === 'user'" />
                                <icon-robot v-else />
                            </div>
                            <div class="bubble">
                                <div class="md-content" v-html="renderMarkdown(msg.content)"></div>
                            </div>
                        </div>

                        <div v-if="loading" class="message-row assistant">
                            <div class="avatar"><icon-robot /></div>
                            <div class="bubble">
                                <a-spin dot />
                                <span class="typing">AI 正在思考…</span>
                            </div>
                        </div>
                    </div>

                    <div class="input-bar">
                        <a-textarea
                            v-model="input"
                            placeholder="输入你的问题，Ctrl/⌘ + Enter 发送"
                            :auto-size="{ minRows: 2, maxRows: 6 }"
                            @keydown.enter.exact.prevent="onEnter"
                            @keydown.ctrl.enter="send"
                            @keydown.meta.enter="send"
                        />
                        <a-button type="primary" :loading="loading" @click="send">
                            <template #icon><icon-send /></template>
                            发送
                        </a-button>
                    </div>
                </a-card>
            </a-col>

            <!-- 右侧 Provider 状态 / 快捷操作 -->
            <a-col :span="6">
                <a-card :bordered="false" title="Provider 池" class="side-card">
                    <div v-if="!providerStatus" class="text-muted">加载中…</div>
                    <template v-else>
                        <div
                            v-for="p in providerStatus.providers"
                            :key="p.name"
                            class="provider-row"
                        >
                            <a-badge
                                :status="badgeStatus(p.status)"
                                :text="p.name"
                            />
                            <span class="provider-meta">
                                {{ p.model }} · 失败 {{ p.failures }}
                            </span>
                        </div>
                        <a-divider style="margin: 12px 0" />
                        <div class="text-muted">
                            <p>当前: <b>{{ providerStatus.current_provider }}</b></p>
                            <p>故障转移: {{ providerStatus.failover_triggered ? '是' : '否' }}</p>
                        </div>
                    </template>
                </a-card>

                <a-card :bordered="false" title="快捷分析" class="side-card">
                    <a-button long @click="quickAnalyze" :loading="analyzing">
                        一键仪表盘洞察
                    </a-button>
                    <a-button long style="margin-top: 8px" @click="quickReport('system_overview')" :loading="reporting">
                        生成系统总览报告
                    </a-button>
                </a-card>
            </a-col>
        </a-row>

        <!-- 报告/洞察弹窗 -->
        <a-modal
            :visible="!!popupContent"
            :title="popupTitle"
            width="720px"
            :footer="false"
            @cancel="popupContent = ''"
        >
            <div class="md-content" v-html="renderMarkdown(popupContent)"></div>
        </a-modal>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
    IconRobot, IconUser, IconSend,
} from '@arco-design/web-vue/es/icon'
import { useStore } from 'vuex'
import { aiApi } from '@/api/modules/ai'
import { renderMarkdown } from '@/utils/markdown'
import type { AIMessage, AIProviderStatus } from '@/types/ai'

const store = useStore()

const messages = ref<AIMessage[]>([])
const input = ref('')
const loading = ref(false)
const analyzing = ref(false)
const reporting = ref(false)
const msgBoxRef = ref<HTMLElement | null>(null)

const providerStatus = computed<AIProviderStatus | null>(
    () => store.state.ai.providerStatus,
)
const isMockMode = computed(() => store.getters['ai/isMockMode'])

const suggestions = [
    '系统当前有多少用户？角色分布如何？',
    '分析最近一周的用户活跃情况',
    '给出权限优化建议',
]

const popupContent = ref('')
const popupTitle = ref('')

function badgeStatus(s: string): 'success' | 'warning' | 'danger' {
    if (s === 'healthy') return 'success'
    if (s === 'degraded') return 'warning'
    return 'danger'
}

function useSuggestion(text: string) {
    input.value = text
    send()
}

function onEnter() {
    // 普通 Enter 换行由 a-textarea 处理；这里只在用户按 Shift+Enter 时放行
    // 由于绑定了 enter.exact.prevent，纯 Enter 不会换行也不会发送
    // 想要换行请用 Shift+Enter
}

async function send() {
    const text = input.value.trim()
    if (!text || loading.value) return

    messages.value.push({ role: 'user', content: text })
    input.value = ''
    loading.value = true
    await scrollToBottom()

    try {
        const res = await aiApi.chat({
            messages: messages.value.map((m) => ({ role: m.role, content: m.content })),
            context: 'chat',
        })
        messages.value.push({
            role: 'assistant',
            content: res.data.reply,
            timestamp: new Date().toISOString(),
        })
        // 若发生故障转移，刷新状态
        if (res.data.failover_triggered) {
            store.dispatch('ai/fetchProviderStatus')
        }
    } catch (e: any) {
        Message.error(e.message || 'AI 调用失败')
    } finally {
        loading.value = false
        await scrollToBottom()
    }
}

async function quickAnalyze() {
    analyzing.value = true
    popupTitle.value = '📊 仪表盘 AI 洞察'
    try {
        const res = await aiApi.getInsights()
        const list = res.data.insights || []
        popupContent.value = list
            .map((i: any) => `- [${i.level?.toUpperCase() || 'INFO'}] ${i.insight}`)
            .join('\n')
        popupContent.value = '### 关键洞察\n\n' + popupContent.value
    } catch (e: any) {
        Message.error(e.message || '洞察生成失败')
    } finally {
        analyzing.value = false
    }
}

async function quickReport(type: string) {
    reporting.value = true
    popupTitle.value = '📝 ' + (type === 'system_overview' ? '系统总览报告' : '报告')
    try {
        const res = await aiApi.generateReport(type)
        popupContent.value = res.data.report
    } catch (e: any) {
        Message.error(e.message || '报告生成失败')
    } finally {
        reporting.value = false
    }
}

async function scrollToBottom() {
    await nextTick()
    if (msgBoxRef.value) {
        msgBoxRef.value.scrollTop = msgBoxRef.value.scrollHeight
    }
}

onMounted(() => {
    store.dispatch('ai/fetchProviderStatus')
})
</script>

<style scoped>
.ai-chat-page {
    padding: 4px;
}
.chat-header h3 {
    margin: 0 0 4px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.hint {
    color: var(--color-text-3);
    font-size: 13px;
    margin-bottom: 16px;
}
.chat-body {
    align-items: stretch;
}
.chat-card {
    display: flex;
    flex-direction: column;
}
:deep(.chat-card .arco-card-body) {
    padding: 0;
    display: flex;
    flex-direction: column;
}
.message-list {
    height: 480px;
    overflow-y: auto;
    padding: 16px;
    background: var(--color-fill-1);
}
.empty-tip {
    text-align: center;
    color: var(--color-text-3);
    padding: 48px 16px;
}
.suggest-list {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 360px;
    margin-left: auto;
    margin-right: auto;
}
.message-row {
    display: flex;
    gap: 10px;
    margin-bottom: 14px;
    align-items: flex-start;
}
.message-row.user {
    flex-direction: row-reverse;
}
.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: var(--color-fill-3);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: var(--color-text-2);
}
.message-row.user .avatar {
    background: rgb(var(--primary-6));
    color: #fff;
}
.bubble {
    max-width: 76%;
    padding: 10px 14px;
    border-radius: 8px;
    background: var(--color-bg-2);
    border: 1px solid var(--color-border-2);
    word-break: break-word;
}
.message-row.user .bubble {
    background: rgb(var(--primary-6));
    color: #fff;
    border-color: transparent;
}
.typing {
    margin-left: 8px;
    color: var(--color-text-3);
}
.input-bar {
    display: flex;
    gap: 8px;
    padding: 12px;
    border-top: 1px solid var(--color-border-2);
}
.side-card {
    margin-bottom: 16px;
}
.provider-row {
    display: flex;
    flex-direction: column;
    margin-bottom: 8px;
}
.provider-meta {
    font-size: 12px;
    color: var(--color-text-3);
    margin-left: 14px;
}
.text-muted {
    color: var(--color-text-3);
    font-size: 13px;
}
:deep(.md-content) {
    line-height: 1.6;
}
:deep(.md-content table) {
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
}
:deep(.md-content th),
:deep(.md-content td) {
    border: 1px solid var(--color-border-2);
    padding: 6px 10px;
}
:deep(.md-content th) {
    background: var(--color-fill-2);
}
:deep(.md-content code) {
    background: var(--color-fill-2);
    padding: 2px 4px;
    border-radius: 3px;
    font-family: 'Consolas', monospace;
}
:deep(.md-content pre) {
    background: var(--color-fill-3);
    padding: 10px;
    border-radius: 6px;
    overflow-x: auto;
}
:deep(.md-content ul),
:deep(.md-content ol) {
    padding-left: 22px;
    margin: 6px 0;
}
.message-row.user :deep(.md-content code) {
    background: rgba(255, 255, 255, 0.2);
}
</style>
