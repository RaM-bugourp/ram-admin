# 05 - Serializer 契约层开发

## 适用场景
API 开发的第一步。先定义 Serializer（前后端契约），再写 ViewSet。

## 关联原则
- 原则2：契约先行 — Serializer 是前后端共同遵守的数据契约
- 原则5：输入验证 — 所有字段白名单验证

## 核心规则
1. **先写 Serializer，再写 View**（铁律）
2. **分三类**：Create 输入 / Update 输入 / Read 输出
3. **Meta.version** 标注版本
4. **所有输入字段有 validator**（白名单验证）
5. **read_only / write_only 明确标注**

## 开发步骤

### 步骤 1：创建输入 Serializer（前端 → 后端）

文件：`apps/rbac/serializers/user_serializers.py`

```python
from rest_framework import serializers
from django.core.validators import RegexValidator

class UserCreateSerializer(serializers.Serializer):
    """创建用户 - 输入契约 v1.0.0"""
    username = serializers.CharField(
        max_length=20, min_length=3,
        validators=[RegexValidator(
            regex=r'^[a-zA-Z0-9_\u4e00-\u9fff]+$',
            message="用户名只能包含字母、数字、下划线和中文"
        )]
    )
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False, default=list
    )

    class Meta:
        version = "v1.0.0"

    def validate_email(self, value):
        allowed_domains = ['company.com', 'partner.com']
        domain = value.split('@')[-1]
        if allowed_domains and domain not in allowed_domains:
            raise serializers.ValidationError(f"仅允许以下域名: {allowed_domains}")
        return value

    def validate_password(self, value):
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("密码必须包含至少一个大写字母")
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("密码必须包含至少一个数字")
        return value

class UserUpdateSerializer(serializers.Serializer):
    """更新用户 - 输入契约 v1.0.0（所有字段可选）"""
    username = serializers.CharField(max_length=20, min_length=3, required=False)
    email = serializers.EmailField(required=False)
    is_active = serializers.BooleanField(required=False)

    class Meta:
        version = "v1.0.0"
```

### 步骤 2：创建输出 Serializer（后端 → 前端）

```python
class UserOutputSerializer(serializers.Serializer):
    """用户信息 - 输出契约 v1.0.0"""
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    roles = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        version = "v1.0.0"

    def get_roles(self, obj):
        return [{"id": r.id, "name": r.name} for r in obj.userrole_set.all()]
```

### 步骤 3：生成前端 TypeScript 类型（从契约手动生成或工具生成）

```typescript
// front-end/src/types/api/user.ts
export interface UserCreateInput {
  username: string
  email: string
  password: string
  role_ids?: number[]
}

export interface UserOutput {
  id: number
  username: string
  email: string
  is_active: boolean
  roles: { id: number; name: string }[]
  created_at: string
}
```

### 步骤 4：Serializer 三大分类速查表

| 类型 | 用途 | 特征 |
|------|------|------|
| **Create** | POST 请求体 | 必填字段多，含密码等敏感字段（write_only） |
| **Update** | PUT/PATCH 请求体 | 所有字段 `required=False` |
| **Output** | GET 响应体 | 所有字段 `read_only=True`，含嵌套对象 |

## 反模式（禁止）
- ❌ 一个 Serializer 同时做输入和输出（职责混杂）
- ❌ 字段无 validator（零信任）
- ❌ 用黑名单验证（`if field != 'bad_value'`）
- ❌ `Meta.version` 缺失（无法追踪契约变更）

## 自检清单
- [ ] 输入 Serializer 每个字段都有明确的 validator？
- [ ] Create / Update / Output 三类 Serializer 分开？
- [ ] 敏感字段标记了 `write_only=True`？
- [ ] 输出字段标记了 `read_only=True`？
- [ ] Meta.version 已标注？
- [ ] 对应的前端 TypeScript 类型已生成？
- [ ] 邮箱/手机号等关键字段有自定义 `validate_xxx` 方法？
- [ ] 密码/金额等有业务校验规则？
