<template>
    <a-modal
        :visible="visible"
        :title="isEdit ? '编辑用户' : '新建用户'"
        width="560px"
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
            <a-form-item field="role_ids" label="角色分配">
                <a-select
                    v-model="form.role_ids"
                    multiple
                    placeholder="请选择角色"
                    :loading="rolesLoading"
                >
                    <a-option
                        v-for="role in allRoles"
                        :key="role.id"
                        :value="role.id"
                    >
                        <a-space>
                            <span>{{ role.name }}</span>
                            <a-tag v-if="role.is_unique" color="red" size="small">唯一</a-tag>
                            <a-tag :color="'arcoblue'" size="small">{{ role.code }}</a-tag>
                        </a-space>
                    </a-option>
                </a-select>
                <template #extra>
                    系统提示：BOSS 角色为唯一角色，同一时间只能分配给一个用户
                </template>
            </a-form-item>
        </a-form>
    </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { Message } from '@arco-design/web-vue'
import { userApi } from '@/api/modules/user'
import { roleApi } from '@/api/modules/role'
import type { UserOutput } from '@/types/user'
import type { RoleOutput } from '@/types/role'

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
const rolesLoading = ref(false)
const allRoles = ref<RoleOutput[]>([])

const form = reactive({
    username: '',
    email: '',
    password: '',
    is_active: true,
    role_ids: [] as number[],
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

async function fetchRoles() {
    rolesLoading.value = true
    try {
        const res = await roleApi.list()
        allRoles.value = res.data
    } catch {
        // ignore
    } finally {
        rolesLoading.value = false
    }
}

// 打开弹窗时加载角色列表并回填数据
watch(
    () => props.visible,
    (v) => {
        if (v) {
            fetchRoles()
            if (props.user) {
                form.username = props.user.username
                form.email = props.user.email
                form.password = ''
                form.is_active = props.user.is_active
                form.role_ids = props.user.roles?.map((r) => r.id) || []
            } else {
                form.username = ''
                form.email = ''
                form.password = ''
                form.is_active = true
                form.role_ids = []
            }
            formRef.value?.clearValidate()
        }
    },
)

async function handleSubmit() {
    const valid = await formRef.value?.validate()
    if (valid !== undefined) return

    try {
        if (isEdit.value) {
            await userApi.update(props.user!.id, {
                username: form.username,
                email: form.email,
                is_active: form.is_active,
                role_ids: form.role_ids,
            })
            Message.success('更新成功')
        } else {
            await userApi.create({
                username: form.username,
                email: form.email,
                password: form.password,
                is_active: form.is_active,
                role_ids: form.role_ids,
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
