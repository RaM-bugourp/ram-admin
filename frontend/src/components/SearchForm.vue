<template>
  <a-card class="search-form" :bordered="false">
    <a-form
      :model="form"
      layout="inline"
      @submit="handleSearch"
    >
      <a-form-item
        v-for="field in fields"
        :key="field.name"
        :label="field.label"
      >
        <!-- 输入框 -->
        <a-input
          v-if="field.type === 'input'"
          v-model="form[field.name]"
          :placeholder="field.placeholder || `请输入${field.label}`"
          :style="{ width: field.width || '200px' }"
          allow-clear
        />

        <!-- 选择框 -->
        <a-select
          v-else-if="field.type === 'select'"
          v-model="form[field.name]"
          :placeholder="field.placeholder || `请选择${field.label}`"
          :style="{ width: field.width || '200px' }"
          allow-clear
        >
          <a-option
            v-for="option in field.options"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </a-option>
        </a-select>

        <!-- 日期选择 -->
        <a-range-picker
          v-else-if="field.type === 'daterange'"
          v-model="form[field.name]"
          :style="{ width: field.width || '260px' }"
        />

        <!-- 数字输入 -->
        <a-input-number
          v-else-if="field.type === 'number'"
          v-model="form[field.name]"
          :placeholder="field.placeholder"
          :style="{ width: field.width || '150px' }"
        />
      </a-form-item>

      <a-form-item>
        <a-space>
          <a-button type="primary" html-type="submit">
            <template #icon><icon-search /></template>
            搜索
          </a-button>
          <a-button @click="handleReset">
            <template #icon><icon-refresh /></template>
            重置
          </a-button>
          <a-button
            v-if="showExport"
            @click="handleExport"
          >
            <template #icon><icon-download /></template>
            导出
          </a-button>
        </a-space>
      </a-form-item>
    </a-form>
  </a-card>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  fields: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Object,
    default: () => ({})
  },
  showExport: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'search', 'reset', 'export'])

const form = reactive({ ...props.modelValue })

// 同步表单数据
watch(form, (val) => {
  emit('update:modelValue', { ...val })
}, { deep: true })

// 初始化表单默认值
props.fields.forEach(field => {
  if (form[field.name] === undefined) {
    form[field.name] = field.default ?? (field.type === 'daterange' ? [] : '')
  }
})

const handleSearch = () => {
  emit('search', { ...form })
}

const handleReset = () => {
  props.fields.forEach(field => {
    form[field.name] = field.default ?? (field.type === 'daterange' ? [] : '')
  })
  emit('reset')
}

const handleExport = () => {
  emit('export', { ...form })
}
</script>

<style scoped>
.search-form {
  margin-bottom: 16px;
}
</style>
