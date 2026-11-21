<template>
    <a-modal
        :visible="visible"
        :title="isEdit ? '编辑角色' : '新建角色'"
        width="520px"
        @ok="handleSubmit"
        @cancel="handleClose"
        :mask-closable="false"
        :ok-loading="submitting"
    >
        <a-form ref="formRef" :model="form" :rules="rules" layout="vertical">
            <a-form-item field="name" label="角色名">
                <a-input
                    v-model="form.name"
                    placeholder="如：超级管理员"
                    :max-length="100"
                />
            </a-form-item>
            <a-form-item field="code" label="角色编码">
                <a-input
                    v-model="form.code"
                    placeholder="如：root（仅小写字母、数字、下划线）"
                    :max-length="50"
                    :disabled="isEdit && isSystemRole"
                />
                <template #extra>
                    编码只能包含小写字母、数字和下划线，且以字母开头
                </template>
            </a-form-item>
            <a-form-item field="description" label="描述">
                <a-textarea
                    v-model="form.description"
                    placeholder="角色的用途说明"
                    :max-length="200"
                    :auto-size="{ minRows: 2, maxRows: 4 }"
                    show-word-limit
                />
            </a-form-item>
            <a-form-item field="is_unique" label="唯一角色">
                <a-switch v-model="form.is_unique" :disabled="isEdit && isSystemRole" />
                <template #extra>
                    开启后，全局只能有一个用户持有该角色（如 BOSS）
                </template>
            </a-form-item>
            <a-form-item label="后台权限"><a-select v-model="form.permissions" multiple :disabled="isEdit && isSystemRole" placeholder="选择闭集后台权限"><a-option v-for="p in catalog" :key="p.code" :value="p.code" :disabled="!p.grantable">{{p.name}} ({{p.code}})</a-option></a-select></a-form-item>
        </a-form>
    </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import client from '@/api/client'
import { Message } from '@arco-design/web-vue'
import { roleApi } from '@/api/modules/role'
import type { RoleOutput } from '@/types/role'

const SYSTEM_ROLES = ['root', 'user', 'boss']

const props = defineProps<{
    visible: boolean
    role: RoleOutput | null
}>()

const emit = defineEmits<{
    (e: 'update:visible', v: boolean): void
    (e: 'success'): void
}>()

const isEdit = computed(() => !!props.role)
const isSystemRole = computed(() => {
    return props.role ? SYSTEM_ROLES.includes(props.role.code) : false
})

const formRef = ref()
const submitting = ref(false)
const catalog = ref<any[]>([])
watch(() => props.visible, async (visible) => { if (visible) { try { const r: any = await client.get('/rbac/permissions/'); catalog.value = r.data } catch(e: any) { Message.error(e.message) } } })
const form = reactive({
    name: '',
    code: '',
    description: '',
    is_unique: false as boolean,
    permissions: [] as string[],
})

const rules = {
    name: [{ required: true, message: '请输入角色名' }],
    code: [
        { required: true, message: '请输入角色编码' },
        {
            match: /^[a-z][a-z0-9_]*$/,
            message: '编码只能包含小写字母、数字和下划线，且以字母开头',
        },
    ],
}

watch(
    () => props.role,
    (role) => {
        if (role) {
            form.name = role.name
            form.code = role.code
            form.description = role.description || ''
            form.is_unique = role.is_unique
            form.permissions = role.permissions || []
        } else {
            form.name = ''
            form.code = ''
            form.description = ''
            form.is_unique = false
            form.permissions = []
        }
    },
    { immediate: true }
)

function handleClose() {
    emit('update:visible', false)
    formRef.value?.resetFields()
}

async function handleSubmit() {
    if (submitting.value) return
    const valid = await formRef.value?.validate()
    if (valid !== undefined) return

    submitting.value = true
    try {
        if (isEdit.value) {
            // 系统角色只允许改描述
            const payload: any = { description: form.description }
            if (!isSystemRole.value) {
                payload.name = form.name
                payload.code = form.code
                payload.is_unique = form.is_unique
                payload.permissions = form.permissions
            }
            await roleApi.update(props.role!.id, payload)
            Message.success('角色已更新')
        } else {
            await roleApi.create({
                name: form.name,
                code: form.code,
                description: form.description,
                is_unique: form.is_unique,
                permissions: form.permissions,
            })
            Message.success('角色已创建')
        }
        emit('success')
        handleClose()
    } catch (e: any) {
        Message.error(e.message || '操作失败')
    } finally {
        submitting.value = false
    }
}
</script>
