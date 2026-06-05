# 13 - 前端 API 层与 TypeScript 类型

## 适用场景
后端 Serializer 定义后，在前端生成对应的 TypeScript 类型和 API 调用函数。

## 关联原则
- 原则2：契约先行 — 前端类型必须从后端 Serializer 生成，保持一致

## 核心规则
1. **TypeScript 类型与后端 Serializer 一一对应**
2. **API 函数按模块组织**
3. **每个 API 函数有明确的输入/输出类型**
4. **运行时类型校验**（防御后端返回格式变化）

## 开发步骤

### 步骤 1：从后端 Serializer 手动生成 TS 类型

对比关系：

```
后端 Serializer                    → 前端 TypeScript
─────────────────────────────────────────────────────
CharField(max_length=20, min_length=3)  → string
EmailField()                        → string
IntegerField()                      → number
BooleanField()                       → boolean
ListField(child=IntegerField())     → number[]
DateTimeField()                     → string (ISO 8601)
SerializerMethodField()             → 需查看 get_xxx 方法确定类型
required=True                       → 必填（无 ?）
required=False / default=...        → 可选（field?）
read_only=True                      → 仅 Output 类型
write_only=True                     → 仅 Input 类型
```

#### 示例：User Serializer → TypeScript

后端：
```python
class UserCreateSerializer(serializers.Serializer):
    username = CharField(max_length=20, min_length=3, validators=[...])
    email = EmailField()
    password = CharField(min_length=8, write_only=True)
    role_ids = ListField(child=IntegerField(), required=False, default=list)

class UserOutputSerializer(serializers.Serializer):
    id = IntegerField(read_only=True)
    username = CharField(read_only=True)
    email = EmailField(read_only=True)
    is_active = BooleanField(read_only=True)
    roles = SerializerMethodField(read_only=True)
    created_at = DateTimeField(read_only=True)
```

前端：
```typescript
// front-end/src/api/types/user.ts

/** 创建用户输入（对应 UserCreateSerializer） */
export interface UserCreateInput {
  username: string        // max_length=20, min_length=3
  email: string           // EmailField
  password: string        // write_only，仅输入
  role_ids?: number[]     // required=False → 可选
}

/** 用户输出（对应 UserOutputSerializer） */
export interface UserOutput {
  id: number
  username: string
  email: string
  is_active: boolean
  roles: UserRoleBrief[]  // SerializerMethodField → 查 get_roles 返回类型
  created_at: string      // DateTimeField → ISO 8601 str
}

export interface UserRoleBrief {
  id: number
  name: string
}
```

### 步骤 2：运行时校验函数（防御性编程）

```typescript
// front-end/src/api/types/user.ts

/** 运行时校验 UserOutput 格式 */
export function isUserOutput(data: unknown): data is UserOutput {
  if (!data || typeof data !== 'object') return false
  const u = data as Record<string, unknown>
  return (
    typeof u.id === 'number' &&
    typeof u.username === 'string' &&
    typeof u.email === 'string' &&
    typeof u.is_active === 'boolean'
  )
}

/** 运行时校验分页响应 */
export function isPaginatedResponse<T>(
  data: unknown,
  itemValidator: (item: unknown) => item is T
): data is { data: T[]; pagination: Pagination } {
  if (!data || typeof data !== 'object') return false
  const d = data as Record<string, unknown>
  return (
    Array.isArray(d.data) &&
    d.data.every(itemValidator) &&
    typeof d.pagination === 'object'
  )
}
```

### 步骤 3：API 函数组织

```typescript
// front-end/src/api/modules/user.ts
import client from '../client'
import type { UserCreateInput, UserOutput } from '../types/user'

export const userApi = {
  /** GET /api/users/ */
  list: (params?: PaginationParams) =>
    client.get<{ data: UserOutput[]; pagination: Pagination }>('/users/', { params }),

  /** GET /api/users/:id/ */
  getById: (id: number) =>
    client.get<UserOutput>(`/users/${id}/`),

  /** POST /api/users/ */
  create: (data: UserCreateInput) =>
    client.post<UserOutput>('/users/', data),

  /** PUT /api/users/:id/ */
  update: (id: number, data: Partial<UserCreateInput>) =>
    client.put<{ id: number; updated: boolean }>(`/users/${id}/`, data),

  /** DELETE /api/users/:id/ */
  delete: (id: number) =>
    client.delete(`/users/${id}/`),

  /** GET /api/users/me/ */
  getMe: () =>
    client.get<UserOutput>('/users/me/'),
}
```

### 步骤 4：契约变更影响分析

当后端 Serializer 变化时：
1. 更新 `Meta.version` 版本号
2. 同步更新前端 TypeScript 类型
3. 检查所有引用该类型的 API 函数和组件
4. 更新运行时校验函数

```
变更类型            → 前端影响
────────────────────────────────────
增加非必填字段      → 仅类型更新（兼容）
增加必填字段         → ⚠️ 所有 create 调用处需更新
删除字段            → ⚠️ 所有使用处需删除
修改字段类型         → ❌ 破坏性变更，需前后端同步
修改字段验证规则    → 前端表单校验需同步
```

## 反模式（禁止）
- ❌ 前端类型由 AI 臆造（必须对照 Serializer 生成）
- ❌ `any` 类型滥用
- ❌ 不校验后端响应数据就使用

## 自检清单
- [ ] TypeScript 类型与后端 Serializer 字段一一对应？
- [ ] 输入类型和输出类型分开？
- [ ] API 函数都有明确的输入/输出类型标注？
- [ ] 有运行时校验函数（防御后端格式变化）？
- [ ] 后端 serializer 变更时同步更新了前端类型？
- [ ] 没有 `any` 类型？
