# 06 - ViewSet 接口层开发

## 适用场景
Serializer + Service + Repository 就绪后，创建 REST API 接口。

## 关联原则
- 原则3：关注点分离 — ViewSet 仅负责请求解析和响应构造
- 原则6：最小权限 — 每个 action 配置权限类

## 核心规则
1. **ViewSet 不写业务逻辑**（只调 Service）
2. **每行 ≤ 3 层调用深度**（request → validate → service → response）
3. **使用 GenericViewSet + Mixins**，不用 ModelViewSet（避免魔法）
4. **每个 action 配独立的 permission_classes**
5. **统一响应格式**

## 统一响应格式

所有接口返回以下 JSON 结构：

```json
// 成功
{ "data": { ... } }

// 分页列表
{ "data": [...], "pagination": { "page": 1, "page_size": 20, "total": 150 } }

// 错误
{ "error": { "code": "VALIDATION_ERROR", "message": "描述", "details": {...} } }
```

### 自定义 Renderer（统一包装）

文件：`apps/common/renderers.py`

```python
from rest_framework.renderers import JSONRenderer

class ApiRenderer(JSONRenderer):
    """统一响应格式：{ data: ... } 或 { error: ... }"""
    
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response')
        if response and 200 <= response.status_code < 300:
            data = {'data': data}
        return super().render(data, accepted_media_type, renderer_context)
```

## 开发步骤

文件：`apps/rbac/views/user_views.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from apps.rbac.serializers.user_serializers import (
    UserCreateSerializer, UserUpdateSerializer, UserOutputSerializer
)
from apps.rbac.services.user_service import UserService
from apps.rbac.permissions.user_permissions import IsSelfOrAdmin

class UserViewSet(viewsets.GenericViewSet):
    """用户管理接口"""
    queryset = ...  # 不使用，但 DRF 要求
    serializer_class = UserOutputSerializer

    def get_permissions(self):
        """按 action 分配权限"""
        permission_map = {
            'list': [IsAuthenticated],
            'retrieve': [IsAuthenticated, IsSelfOrAdmin],
            'create': [IsAdminUser],
            'update': [IsAdminUser],
            'destroy': [IsAdminUser],
        }
        return [p() for p in permission_map.get(self.action, [IsAuthenticated])]

    def get_serializer_class(self):
        """按 action 选择 Serializer"""
        return {
            'create': UserCreateSerializer,
            'update': UserUpdateSerializer,
        }.get(self.action, UserOutputSerializer)

    def list(self, request):
        """GET /api/users/ - 用户列表"""
        users = UserService().list_users()
        serializer = UserOutputSerializer(users, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """GET /api/users/{id}/ - 用户详情"""
        user = UserService().get_user_detail(pk)
        if not user:
            return Response(
                {"error": {"code": "NOT_FOUND", "message": "用户不存在"}},
                status=404
            )
        serializer = UserOutputSerializer(user)
        return Response(serializer.data)

    def create(self, request):
        """POST /api/users/ - 创建用户"""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = UserService().create_user(serializer.validated_data)
        return Response(result, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        """PUT /api/users/{id}/ - 更新用户"""
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        UserService().update_user(pk, serializer.validated_data)
        return Response({"data": {"id": pk, "updated": True}})

    def destroy(self, request, pk=None):
        """DELETE /api/users/{id}/ - 软删除用户"""
        UserService().delete_user(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """GET /api/users/me/ - 当前用户"""
        serializer = UserOutputSerializer(request.user)
        return Response(serializer.data)
```

## 反模式（禁止）
- ❌ ViewSet 里写 `if user.role == 'admin'` → 放 Service
- ❌ ViewSet 里直接 `User.objects.create()` → 通过 Service
- ❌ 一个 action 做多件事 → 拆为多个 action
- ❌ 不区分 create/update Serializer
- ❌ 用 ModelViewSet（行为不透明）

## 自检清单
- [ ] 每个 action 有独立的 permissions？
- [ ] 不包含业务逻辑（if/else 判断）？
- [ ] create/update 分别用不同的 Serializer？
- [ ] 错误响应格式统一？（`{error: {code, message}}`）
- [ ] 敏感 action（delete/create）有 `@action` 装饰？
- [ ] 使用 `GenericViewSet` 而不是 `ModelViewSet`？
- [ ] Retrieve/List 用的 OutputSerializer？
- [ ] URL 路由符合 RESTful 规范？
