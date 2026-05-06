# RaM Admin 开发指南

---

## 一、开发环境配置

### 1.1 IDE 推荐

- **VS Code** + 扩展：
  - Python (Microsoft)
  - Vue - Official
  - ESLint
  - Prettier

- **PyCharm** + 插件：
  - Vue.js

### 1.2 代码格式化

**Python (black)**:
```bash
pip install black
black backend/
```

**JavaScript (prettier)**:
```bash
npm install -D prettier
npx prettier --write frontend/src/
```

### 1.3 Git 配置

```bash
# 提交前检查
git add .
git commit -m "feat: 添加新功能"
```

---

## 二、后端开发

### 2.1 添加新模块

**使用代码生成器**:
```bash
cd backend
python scripts/codegen.py <app> <Model> --fields name:str,price:decimal
```

**手动创建**:
```bash
# 创建应用
python manage.py startapp apps/<app_name>

# 目录结构
apps/<app_name>/
├── __init__.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
├── tests.py
└── migrations/
    └── __init__.py
```

### 2.2 模型设计

```python
# apps/shop/models.py

from django.db import models
from packages.core.foundation.models import BaseAuditModel

class Product(BaseAuditModel):
    """
    商品模型
    
    继承 BaseAuditModel 自动获得：
    - created_at / updated_at (时间戳)
    - created_by / updated_by (用户)
    - owner_organization (组织)
    - is_deleted / deleted_at (软删除)
    """
    
    name = models.CharField('商品名称', max_length=200)
    price = models.DecimalField('价格', max_digits=10, decimal_places=2)
    stock = models.IntegerField('库存', default=0)
    description = models.TextField('描述', blank=True)
    
    class Meta:
        db_table = 'shop_product'
        verbose_name = '商品'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return self.name
```

### 2.3 序列化器

```python
# apps/shop/serializers.py

from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    """商品完整序列化器"""
    
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']

class ProductListSerializer(serializers.ModelSerializer):
    """商品列表序列化器（字段精简，提升性能）"""
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'created_at']
```

### 2.4 视图集

```python
# apps/shop/views.py

from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from packages.core.foundation.mixins import AuditOwnerPopulateMixin
from .models import Product
from .serializers import ProductSerializer, ProductListSerializer

class ProductViewSet(AuditOwnerPopulateMixin, viewsets.ModelViewSet):
    """
    商品视图集
    
    AuditOwnerPopulateMixin 提供：
    - perform_create 时自动填充 created_by
    - perform_update 时自动填充 updated_by
    """
    
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    list_serializer_class = ProductListSerializer
    
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'stock']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """按动作选择序列化器"""
        if self.action == 'list':
            return self.list_serializer_class
        return self.serializer_class
```

### 2.5 URL 配置

```python
# apps/shop/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

### 2.6 注册应用

```python
# settings.py
INSTALLED_APPS = [
    ...
    'apps.shop',
]

# urls.py
urlpatterns = [
    ...
    path('api/shop/', include('apps.shop.urls')),
]
```

### 2.7 数据库迁移

```bash
python manage.py makemigrations shop
python manage.py migrate
```

---

## 三、前端开发

### 3.1 目录结构

```
frontend/src/
├── api/              # API 接口
│   ├── article.js
│   └── product.js
├── views/            # 页面组件
│   ├── article/
│   │   ├── list.vue
│   │   └── detail.vue
│   └── product/
│       └── list.vue
├── components/       # 通用组件
│   ├── CrudTable.vue
│   └── SearchForm.vue
├── layout/           # 布局组件
│   └── content/
│       └── index.vue
├── router/           # 路由配置
│   └── index.js
├── store/            # Vuex 状态
│   └── modules/
│       ├── user.js
│       └── menu.js
└── utils/            # 工具函数
    └── request.js
```

### 3.2 API 封装

```javascript
// frontend/src/api/product.js

import request from '@/utils/request'

export function listProducts(params) {
  return request.get('/shop/products/', { params })
}

export function createProduct(data) {
  return request.post('/shop/products/', data)
}

export function updateProduct(id, data) {
  return request.patch(`/shop/products/${id}/`, data)
}

export function deleteProduct(id) {
  return request.delete(`/shop/products/${id}/`)
}
```

### 3.3 页面组件

```vue
<!-- frontend/src/views/product/list.vue -->

<template>
  <div class="product-list">
    <!-- 搜索表单 -->
    <a-card class="search-card">
      <a-form layout="inline">
        <a-form-item label="名称">
          <a-input v-model="searchForm.name" placeholder="搜索名称" />
        </a-form-item>
        <a-form-item>
          <a-button type="primary" @click="handleSearch">搜索</a-button>
          <a-button @click="handleReset">重置</a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 数据表格 -->
    <a-card class="table-card">
      <template #title>
        <a-button type="primary" @click="handleCreate">
          <template #icon><icon-plus /></template>
          新增
        </a-button>
      </template>

      <a-table
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        @page-change="handlePageChange"
      >
        <template #actions="{ record }">
          <a-button type="text" @click="handleEdit(record)">编辑</a-button>
          <a-popconfirm content="确定删除？" @ok="handleDelete(record.id)">
            <a-button type="text" status="danger">删除</a-button>
          </a-popconfirm>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { listProducts, deleteProduct } from '@/api/product'
import { Message } from '@arco-design/web-vue'

const columns = [
  { title: 'ID', dataIndex: 'id' },
  { title: '名称', dataIndex: 'name' },
  { title: '价格', dataIndex: 'price' },
  { title: '库存', dataIndex: 'stock' },
  { title: '操作', slotName: 'actions' },
]

const tableData = ref([])
const loading = ref(false)
const pagination = reactive({ current: 1, pageSize: 20, total: 0 })
const searchForm = reactive({ name: '' })

const fetchData = async () => {
  loading.value = true
  try {
    const res = await listProducts({
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm,
    })
    tableData.value = res.list
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  fetchData()
}

const handleReset = () => {
  searchForm.name = ''
  handleSearch()
}

const handlePageChange = (page) => {
  pagination.current = page
  fetchData()
}

const handleCreate = () => {
  // 打开创建弹窗
}

const handleEdit = (record) => {
  // 打开编辑弹窗
}

const handleDelete = async (id) => {
  await deleteProduct(id)
  Message.success('删除成功')
  fetchData()
}

onMounted(fetchData)
</script>
```

### 3.4 使用 CrudTable 组件

```vue
<!-- 简化版：使用通用 CRUD 表格 -->

<template>
  <CrudTable
    :columns="columns"
    api-url="/api/shop/products/"
    :search-fields="searchFields"
    :form-fields="formFields"
  />
</template>

<script setup>
const columns = [
  { title: '名称', dataIndex: 'name' },
  { title: '价格', dataIndex: 'price' },
  { title: '库存', dataIndex: 'stock' },
]

const searchFields = [
  { name: 'name', label: '名称', type: 'input' },
]

const formFields = [
  { name: 'name', label: '名称', type: 'input', required: true },
  { name: 'price', label: '价格', type: 'number', required: true },
  { name: 'stock', label: '库存', type: 'number' },
]
</script>
```

---

## 四、测试

### 4.1 后端测试

```python
# backend/tests/test_shop.py

import pytest

class TestProduct:
    def test_list_products(self, authenticated_client):
        response = authenticated_client.get('/api/shop/products/')
        assert response.status_code == 200

    def test_create_product(self, authenticated_client):
        response = authenticated_client.post('/api/shop/products/', {
            'name': '测试商品',
            'price': 99.99,
            'stock': 100,
        })
        assert response.status_code == 201
```

运行测试:
```bash
cd backend
pytest
```

### 4.2 前端测试

```javascript
// frontend/src/__tests__/product.test.js

import { mount } from '@vue/test-utils'
import ProductList from '@/views/product/list.vue'

test('renders product list', () => {
  const wrapper = mount(ProductList)
  expect(wrapper.find('.product-list').exists()).toBe(true)
})
```

---

## 五、调试技巧

### 5.1 后端调试

```python
# 临时打印调试
import pprint
pprint.pprint(locals())

# Django shell
python manage.py shell

# 查看生成的 SQL
from django.db import connection
connection.queries
```

### 5.2 前端调试

```javascript
// Vue DevTools
// 安装 Vue DevTools 浏览器扩展

// 控制台调试
console.log('data:', data)
debugger  // 断点
```

---

## 六、常见问题

### Q1: 迁移冲突

```bash
# 重置迁移
python manage.py migrate --fake
python manage.py makemigrations
python manage.py migrate
```

### Q2: 循环导入

```python
# 使用字符串引用
'apps.user.models.User'  # 而不是直接 import User
```

### Q3: 前端热更新不生效

```bash
# 清除缓存
rm -rf frontend/node_modules/.vite
npm run dev
```
