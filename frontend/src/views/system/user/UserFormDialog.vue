<template>
    <a-modal
        :visible="visible"
        :title="isEdit ? '编辑用户' : '新建用户'"
        width="520px"
        @ok="handleSubmit"
        @cancel="handleClose"
        :mask-closable="false"
    >
        <a-form ref="formRef" :model="form" :rules="rules" layout="vertical">
            <a-form-item field="username" label="用户名">
                <a-input v-model="form.username" placeholder="至少3位" :max-length="150" />
            </a-form-item>
            <a-form-item field="email" label="邮箱">
                <a-input v-model="form.email" placeholder="user@example.com" />
            </a-form-item>
            <a-form-item v-if="!isEdit" field="password" label="密码">
                <a-input-password v-model="form.password" placeholder="至少6位" />
            </a-form-item>
            <a-form-item field="is_active" label="启用状态">
                <a-switch v-model="form.is_active" :checked-text="'启用'" :unchecked-text="'禁用'" />
            </a-form-item>
        </a-form>
    </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { userApi } from '@/api/modules/user'
import type { UserOutput } from '@/types/user'

const props = defineProps<{
    visible: boolean
    user: UserOutput | null
}>()

const emit = defineEmits<{
    (e: 'update:visible', v: boolean): void
    (e: 'success'): void
}>()

const isEdit = computed(() => !!props.user)

const formRef = ref()
const form = reactive({
    username: '',
    email: '',
    password: '',
    is_active: true,
})

const rules = {
    username: [
        { required: true, message: '请输入用户名' },
        { minLength: 3, message: '至少3位' },
    ],
    email: [
        { required: true, message: '请输入邮箱' },
        { type: 'email' as const, message: '邮箱格式不正确' },
    ],
    password: [
        { required: true, message: '请输入密码' },
        { minLength: 6, message: '至少6位' },
    ],
}

// 打开弹窗时回填数据
watch(
    () => props.visible,
    (v) => {
        if (v) {
            if (props.user) {
                form.username = props.user.username
                form.email = props.user.email
                form.password = ''
                form.is_active = props.user.is_active
            } else {
                form.username = ''
                form.email = ''
                form.password = ''
                form.is_active = true
            }
            formRef.value?.clearValidate()
        }
    },
)

async function handleSubmit() {
    const valid = await formRef.value?.validate()
    if (valid !== undefined) return // 校验不通过

    try {
        if (isEdit.value) {
            await userApi.update(props.user!.id, {
                username: form.username,
                email: form.email,
                is_active: form.is_active,
            })
            Message.success('更新成功')
        } else {
            await userApi.create({
                username: form.username,
                email: form.email,
                password: form.password,
                is_active: form.is_active,
            })
            Message.success('创建成功')
        }
        emit('success')
        handleClose()
    } catch (e: any) {
        Message.error(e.message || '操作失败')
    }
}

function handleClose() {
    emit('update:visible', false)
}
</script>
