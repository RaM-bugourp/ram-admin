<template>
  <div class="article-list">
    <a-card>
      <template #title>
        <div class="card-title">
          <span>文章列表</span>
          <a-button type="primary" @click="showCreate = true">
            <template #icon><icon-plus /></template>
            新建文章
          </a-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <a-input-search
          v-model="searchKey"
          placeholder="搜索标题/内容"
          style="width: 280px"
          @search="loadData"
          @press-enter="loadData"
        />
        <a-select
          v-model="filterStatus"
          placeholder="状态"
          style="width: 120px"
          allow-clear
          @change="loadData"
        >
          <a-option value="draft">草稿</a-option>
          <a-option value="published">已发布</a-option>
          <a-option value="archived">已归档</a-option>
        </a-select>
        <a-button @click="resetFilter">重置</a-button>
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
        <template #status="{ record }">
          <a-tag :color="statusColor[record.status]">
            {{ record.status_text }}
          </a-tag>
        </template>
        <template #tags="{ record }">
          <a-tag v-for="tag in record.tags.split(',')" :key="tag" size="small">
            {{ tag }}
          </a-tag>
        </template>
        <template #actions="{ record }">
          <a-button type="text" size="small" @click="handleView(record)">
            查看
          </a-button>
          <a-button type="text" size="small" @click="handleEdit(record)">
            编辑
          </a-button>
          <a-button
            v-if="record.status === 'draft'"
            type="text"
            size="small"
            @click="handlePublish(record)"
          >
            发布
          </a-button>
          <a-popconfirm content="确定删除？" @ok="handleDelete(record)">
            <a-button type="text" size="small" status="danger">删除</a-button>
          </a-popconfirm>
        </template>
      </a-table>
    </a-card>

    <!-- 创建/编辑弹窗 -->
    <a-modal
      v-model:visible="showCreate"
      :title="editingId ? '编辑文章' : '新建文章'"
      :width="640"
      @before-ok="handleSave"
    >
      <a-form :model="form" layout="vertical">
        <a-form-item label="标题" required>
          <a-input v-model="form.title" placeholder="请输入标题" />
        </a-form-item>
        <a-form-item label="内容">
          <a-textarea v-model="form.content" :rows="6" placeholder="请输入内容" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model="form.status">
            <a-option value="draft">草稿</a-option>
            <a-option value="published">已发布</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="标签">
          <a-input v-model="form.tags" placeholder="多个标签用逗号分隔" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import {
  getArticleList, createArticle, updateArticle,
  deleteArticle, publishArticle,
} from '@/api/article'

const columns = [
  { title: 'ID', dataIndex: 'id', width: 60 },
  { title: '标题', dataIndex: 'title' },
  { title: '状态', slotName: 'status', width: 90 },
  { title: '标签', slotName: 'tags', width: 160 },
  { title: '作者', dataIndex: 'created_by_name', width: 100 },
  { title: '创建时间', dataIndex: 'created_at', width: 160 },
  { title: '操作', slotName: 'actions', width: 200 },
]

const tableData = ref([])
const loading = ref(false)
const searchKey = ref('')
const filterStatus = ref('')
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const showCreate = ref(false)
const editingId = ref(null)

const form = reactive({ title: '', content: '', status: 'draft', tags: '' })

const statusColor = { draft: 'gray', published: 'green', archived: 'orange' }

const loadData = async () => {
  loading.value = true
  try {
    const res = await getArticleList({
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchKey.value,
      status: filterStatus.value,
    })
    // axios 拦截器已适配 DRF 分页格式
    tableData.value = res.list || res.results || []
    pagination.total = res.total || res.count || 0
  } catch {
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const onPageChange = (page) => { pagination.current = page; loadData() }
const onPageSizeChange = (size) => { pagination.pageSize = size; pagination.current = 1; loadData() }
const resetFilter = () => { searchKey.value = ''; filterStatus.value = ''; loadData() }

const handleView = (record) => { /* TODO */ }
const handleEdit = (record) => {
  editingId.value = record.id
  Object.assign(form, { title: record.title, content: record.content, status: record.status, tags: record.tags })
  showCreate.value = true
}

const handleSave = async (done) => {
  try {
    if (editingId.value) {
      await updateArticle(editingId.value, form)
      Message.success('更新成功')
    } else {
      await createArticle(form)
      Message.success('创建成功')
    }
    showCreate.value = false
    done(true)
    loadData()
  } catch {
    done(false)
  }
}

const handlePublish = async (record) => {
  await publishArticle(record.id)
  Message.success('已发布')
  loadData()
}

const handleDelete = async (record) => {
  await deleteArticle(record.id)
  Message.success('已删除')
  loadData()
}

loadData()
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
