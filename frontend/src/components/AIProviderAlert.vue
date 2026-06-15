<template>
    <a-alert
        v-if="visible"
        type="warning"
        banner
        closable
        @close="dismissed = true"
    >
        <template #title>⚠️ AI Provider 故障转移</template>
        {{ message }}
    </a-alert>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const dismissed = ref(false)

const visible = computed(
    () => !dismissed.value && store.getters['ai/isFailoverActive'],
)

const message = computed(() => {
    const status = store.state.ai.providerStatus
    if (!status) return ''
    const failed = status.providers.filter((p: any) => p.status === 'failed')
    if (failed.length === 0) return '部分 Provider 处于降级状态'
    const names = failed.map((p: any) => p.name).join('、')
    return `Provider [${names}] 失败，已自动切换到 "${status.current_provider}"`
})
</script>
