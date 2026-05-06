# RaM Admin API 文档

> **在线文档**: http://localhost:8000/api/docs/
> **ReDoc**: http://localhost:8000/api/redoc/
> **OpenAPI Schema**: http://localhost:8000/api/schema/

---

## 一、认证接口

### 1.1 登录

```
POST /api/auth/login/
```

**请求体**:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_superuser": true,
  "roles": ["admin"],
  "permission_codes": ["*"]
}
```

### 1.2 获取用户信息

```
GET /api/auth/user_info/
```

**响应**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_superuser": true,
  "roles": [
    {
      "id": 1,
      "name": "管理员",
      "code": "admin"
    }
  ],
  "permission_codes": ["*"]
}
```

### 1.3 登出

```
POST /api/auth/logout/
```

**响应**:
```json
{
  "message": "登出成功"
}
```

---

## 二、RBAC 接口

### 2.1 菜单管理

#### 获取菜单列表

```
GET /api/rbac/menus/
```

**响应**:
```json
{
  "list": [
    {
      "id": 1,
      "title": "系统管理",
      "path": "/system",
      "component": "",
      "icon": "icon-setting",
      "sort": 1,
      "is_hidden": false,
      "parent": null
    }
  ],
  "total": 10
}
```

#### 获取菜单树

```
GET /api/rbac/menus/tree/
```

**响应**:
```json
[
  {
    "id": 1,
    "title": "系统管理",
    "path": "/system",
    "icon": "icon-setting",
    "children": [
      {
        "id": 2,
        "title": "用户管理",
        "path": "/system/user",
        "component": "system/user/index",
        "icon": "icon-user"
      }
    ]
  }
]
```

#### 创建菜单

```
POST /api/rbac/menus/
```

**请求体**:
```json
{
  "title": "文章管理",
  "path": "/article",
  "component": "article/index",
  "icon": "icon-file",
  "sort": 10,
  "parent": null
}
```

### 2.2 角色管理

#### 获取角色列表

```
GET /api/rbac/roles/
```

#### 创建角色

```
POST /api/rbac/roles/
```

**请求体**:
```json
{
  "name": "编辑",
  "code": "editor",
  "description": "内容编辑角色",
  "permissions": [1, 2, 3],
  "menus": [1, 2, 3]
}
```

### 2.3 权限管理

#### 获取权限列表

```
GET /api/rbac/permissions/
```

#### 获取权限码树

```
GET /api/rbac/permissions/code_tree/
```

---

## 三、文章接口

### 3.1 文章列表

```
GET /api/article/articles/
```

**查询参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认 1 |
| page_size | int | 每页数量，默认 20 |
| title | string | 标题搜索 |
| status | string | 状态过滤：draft/published |
| ordering | string | 排序：created_at / -created_at |

**响应**:
```json
{
  "list": [
    {
      "id": 1,
      "title": "文章标题",
      "summary": "文章摘要",
      "content": "文章内容",
      "status": "published",
      "created_at": "2026-04-20T10:00:00Z",
      "updated_at": "2026-04-20T11:00:00Z",
      "created_by": {
        "id": 1,
        "username": "admin"
      }
    }
  ],
  "total": 100,
  "page": 1
}
```

### 3.2 创建文章

```
POST /api/article/articles/
```

**请求体**:
```json
{
  "title": "新文章",
  "summary": "文章摘要",
  "content": "文章正文内容...",
  "status": "draft"
}
```

### 3.3 更新文章

```
PATCH /api/article/articles/{id}/
```

**请求体**:
```json
{
  "title": "更新后的标题",
  "status": "published"
}
```

### 3.4 删除文章

```
DELETE /api/article/articles/{id}/
```

> 注意：实际执行软删除，数据不会物理删除

---

## 四、系统接口

### 4.1 健康检查

```
GET /health/
```

**响应**:
```json
{
  "status": "ok"
}
```

### 4.2 系统信息

```
GET /api/system/info/
```

**响应**:
```json
{
  "version": "1.0.0",
  "django_version": "5.2",
  "python_version": "3.12",
  "debug": false
}
```

---

## 五、通用说明

### 5.1 认证方式

使用 Django Session 认证：

```javascript
// 前端请求时携带 credentials
fetch('/api/auth/user_info/', {
  credentials: 'include'  // 携带 cookie
})
```

### 5.2 CSRF 保护

所有 POST/PUT/PATCH/DELETE 请求需携带 CSRF Token：

```javascript
// 从 cookie 获取 CSRF Token
const csrfToken = document.cookie
  .split('; ')
  .find(row => row.startsWith('csrftoken='))
  ?.split('=')[1]

// 请求头携带
fetch('/api/article/articles/', {
  method: 'POST',
  headers: {
    'X-CSRFToken': csrfToken,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)
})
```

### 5.3 分页格式

DRF 标准分页响应被前端适配为：

```json
{
  "list": [...],      // 数据列表
  "total": 100,       // 总数
  "page": 1,          // 当前页
  "totalPages": 10    // 总页数
}
```

### 5.4 错误格式

```json
{
  "detail": "错误信息"
}
```

或字段错误：

```json
{
  "title": ["该字段不能为空"],
  "content": ["内容长度不能少于10个字符"]
}
```

### 5.5 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无响应体） |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |
