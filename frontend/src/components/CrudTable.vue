<template>
  <a-card>
    <template #title>
      <div class="card-title">
        <span>{{ title }}</span>
        <a-button
          v-if="showCreate"
          v-permission="createPermission"
          type="primary"
          @click="handleCreate"
        >
          <template #icon><icon-plus /></template>
          新建
        </a-button>
      </div>
    </template>

    <!-- 搜索栏 -->
    <div v-if="searchFields.length" class="search-bar">
      <template v-for="field in searchFields" :key="field.key">
        <a-input-search
          v-if="field.type === 'search'"
          v-model="searchParams[field.key]"
          :placeholder="field.placeholder || '搜索'"
          :style="{ width: field.width || '200px' }"
          @search="loadData"
          @press-enter="loadData"
        />
        <a-select
          v-else-if="field.type === 'select'"
          v-model="searchParams[field.key]"
          :placeholder="field.placeholder || '请选择'"
          :style="{ width: field.width || '120px' }"
          allow-clear
          @change="loadData"
        >
          <a-option
            v-for="opt in field.options"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </a-option>
        </a-select>
      </template>
      <a-button @click="resetSearch">重置</a-button>
    </div>

    <!-- 表格 -->
    <a-table
      :columns="columns"
      :data="tableData"
      :loading="loading"
      :pagination="pagination"
      @page-change="onPageChange"
      @page-size-change="onPageSizeChange"
      row-key="id"
      stripe
    >
      <!-- 动态插槽 -->
      <template v-for="slot in customSlots" :key="slot" #[slot]="{ record }">
        <slot :name="slot" :record="record" />
      </template>

      <!-- 操作列 -->
      <template v-if="showActions" #actions="{ record }">
        <slot name="actions" :record="record" :handle-edit="() => handleEdit(record)" :handle-delete="() => handleDelete(record)">
          <a-button type="text" size="small" @click="handleEdit(record)">
            编辑
          </a-button>
          <a-popconfirm content="确定删除？" @ok="handleDelete(record)">
            <a-button type="text" size="small" status="danger">删除</a-button>
          </a-popconfirm>
        </slot>
      </template>
    </a-table>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:visible="showModal"
      :title="editingId ? '编辑' : '新建'"
      :width="modalWidth"
      @before-ok="handleSave"
    >
      <slot name="form" :form="form" :editing="!!editingId" />
    </a-modal>
  </a-card>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Message } from '@arco-design/web-vue'

const props = defineProps({
  title: { type: String, default: '数据列表' },
  columns: { type: Array, required: true },
  api: { type: Object, required: true }, // { list, create, update, delete }
  searchFields: { type: Array, default: () => [] },
  showCreate: { type: Boolean, default: true },
  showActions: { type: Boolean, default: true },
  createPermission: { type: String, default: '' },
  modalWidth: { type: Number, default: 640 },
  defaultForm: { type: Function, default: () => ({}) },
})

const emit = defineEmits(['created', 'updated', 'deleted'])

// 状态
const tableData = ref([])
const loading = ref(false)
const showModal = ref(false)
const editingId = ref(null)
const form = reactive(props.defaultForm())
const searchParams = reactive({})

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
})

// 自定义插槽名（排除 actions）
const customSlots = computed(() =>
  props.columns
    .filter((c) => c.slotName && c.slotName !== 'actions')
    .map((c) => c.slotName)
)

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await props.api.list({
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchParams,
    })
    tableData.value = res.list || res.results || []
    pagination.total = res.total || res.count || 0
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

// 分页事件
const onPageChange = (page) => {
  pagination.current = page
  loadData()
}
const onPageSizeChange = (size) => {
  pagination.pageSize = size
  pagination.current = 1
  loadData()
}

// 重置搜索
const resetSearch = () => {
  Object.keys(searchParams).forEach((k) => delete searchParams[k])
  props.searchFields.forEach((f) => {
    searchParams[f.key] = ''
  })
  loadData()
}

// 创建
const handleCreate = () => {
  editingId.value = null
  Object.assign(form, props.defaultForm())
  showModal.value = true
}

// 编辑
const handleEdit = (record) => {
  editingId.value = record.id
  Object.assign(form, record)
  showModal.value = true
}

// 保存
const handleSave = async (done) => {
  try {
    if (editingId.value) {
      await props.api.update(editingId.value, form)
      Message.success('更新成功')
      emit('updated', form)
    } else {
      await props.api.create(form)
      Message.success('创建成功')
      emit('created', form)
    }
    showModal.value = false
    done(true)
    loadData()
  } catch {
    done(false)
  }
}

// 删除
const handleDelete = async (record) => {
  await props.api.delete(record.id)
  Message.success('已删除')
  emit('deleted', record)
  loadData()
}

// 初始化
onMounted(() => {
  props.searchFields.forEach((f) => {
    searchParams[f.key] = ''
  })
  loadData()
})

// 暴露方法
defineExpose({ loadData, refresh: loadData })
</script>

<style scoped>
.card-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
