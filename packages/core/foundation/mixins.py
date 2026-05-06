"""
DRF ViewSet Mixin 层
══════════════════════════════════════════════════════════════════

本模块提供 4 个 Mixin，用于在 DRF ViewSet 层面实现通用能力：

    class ProductViewSet(
        AuditOwnerPopulateMixin,   # 自动填充创建人/组织
        SoftDeleteMixin,           # 软删除 + 查询过滤
        ActionSerializerMixin,      # 按动作选择不同序列化器
        ModelViewSet
    ):
        ...

══════════════════════════════════════════════════════════════════

执行顺序（请求生命周期中的位置）：
─────────────────────────────────────
请求 → Authentication（认证） → Permission（权限） →
  → AuditOwnerPopulateMixin.perform_create()  ← 这里填充 created_by
  → serializer.save()                         ← 数据写入 DB
  → AuditOwnerPopulateMixin.perform_update()  ← 这里更新 updated_by
  → 响应

注意：Mixin 的 perform_create / perform_update 是在权限检查之后、
serializer.save() 之前执行的，所以不会污染已删除数据的权限。
"""

from rest_framework import viewsets
from rest_framework import serializers


# ─────────────────────────────────────────────────────────────────
# 辅助函数（内部使用）
# ─────────────────────────────────────────────────────────────────

def _model_has_field(model, field_name):
    """
    检查模型是否有某个字段。

    Django 的 _meta.get_field() 会在字段不存在时抛异常，
    所以用 try/except 包装成布尔返回值。
    """
    try:
        model._meta.get_field(field_name)
        return True
    except Exception:
        return False


def _get_user_primary_org(user):
    """
    获取用户的主组织。

    如果用户属于多个组织（UserOrganization），返回 is_primary=True 的那个。
    如果没有主组织，返回 None（owner_organization 字段允许为空）。

    这里用延迟导入（import inside function）避免循环引用。
    因为 rbac.models 可能还没加载完，提前导入会报错。
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    try:
        from apps.rbac.models import UserOrganization
        relation = UserOrganization.objects.filter(
            user=user,
            is_primary=True
        ).select_related('organization').first()
        return relation.organization if relation else None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────
# SoftDeleteMixin（ViewSet 层）
# ─────────────────────────────────────────────────────────────────

class SoftDeleteMixin(viewsets.GenericViewSet):
    """
    ViewSet 层面的软删除。

    配合 models.py 中的 SoftDeleteMixin 使用：
    - models.SoftDeleteMixin：负责 delete() 方法改为软删除
    - SoftDeleteMixin（这里）：负责 get_queryset() 过滤已删除记录

    为什么要在 ViewSet 层也加过滤？
        —— 防止用户通过 API 直接查已删除的数据
        —— 已有数据的保护（Django ORM 层面无法限制）
    """

    def get_queryset(self):
        """
        自动过滤已删除记录。

        Django REST Framework 的 list/retrieve/destroy 都调用 get_queryset()。
        重写这里，所有查询自动排除 is_deleted=True 的记录。
        """
        queryset = super().get_queryset()
        model = queryset.model

        # 只有模型有 is_deleted 字段时才过滤
        if _model_has_field(model, 'is_deleted'):
            return queryset.filter(is_deleted=False)

        return queryset

    def perform_destroy(self, instance):
        """
        重写删除行为 —— 软删除。

        DRF 的 destroy() 方法默认调用 instance.delete()（真实删除）。
        重写后改为设置 is_deleted=True。
        """
        if _model_has_field(instance.__class__, 'is_deleted'):
            instance.is_deleted = True
            from django.utils import timezone
            instance.deleted_at = timezone.now()
            instance.save(update_fields=['is_deleted', 'deleted_at'])
        else:
            # 模型没有软删除字段时，保留真实删除
            instance.delete()


# ─────────────────────────────────────────────────────────────────
# AuditOwnerPopulateMixin（自动填充审计字段）
# ─────────────────────────────────────────────────────────────────

class AuditOwnerPopulateMixin(viewsets.GenericViewSet):
    """
    在 create/update 时自动填充审计字段。

    perform_create() —— 自动填充：
        created_by     = 当前登录用户
        updated_by     = 当前登录用户
        owner_organization = 用户的主组织（如果没有手动指定）

    perform_update() —— 自动填充：
        updated_by     = 当前登录用户

    为什么用 perform_create 而不是 get_serializer 的 save_kwargs？
        —— perform_create 在权限检查之后、写入 DB 之前执行
        —— 逻辑更清晰，不污染 serializer 的职责
    """

    def perform_create(self, serializer):
        """创建时填充 created_by / updated_by / owner_organization"""
        model = serializer.Meta.model
        user = getattr(self.request, 'user', None)
        extra = {}

        if user and getattr(user, 'is_authenticated', False):
            # created_by：谁创建的
            if _model_has_field(model, 'created_by'):
                extra['created_by'] = user

            # updated_by：谁更新的（创建时也填）
            if _model_has_field(model, 'updated_by'):
                extra['updated_by'] = user

            # owner_organization：如果用户没有手动指定，自动填主组织
            if (_model_has_field(model, 'owner_organization')
                    and not serializer.validated_data.get('owner_organization')):
                org = _get_user_primary_org(user)
                if org is not None:
                    extra['owner_organization'] = org

        # 只有 extra 非空时才传入 save()，避免参数冲突
        serializer.save(**extra)

    def perform_update(self, serializer):
        """更新时填充 updated_by"""
        model = serializer.Meta.model
        user = getattr(self.request, 'user', None)
        extra = {}

        if user and getattr(user, 'is_authenticated', False):
            if _model_has_field(model, 'updated_by'):
                extra['updated_by'] = user

        serializer.save(**extra)


# ─────────────────────────────────────────────────────────────────
# ActionSerializerMixin（按动作选择序列化器）
# ─────────────────────────────────────────────────────────────────

class ActionSerializerMixin(viewsets.GenericViewSet):
    """
    根据 action 自动选择不同的 Serializer。

    用法：
        class ProductViewSet(ActionSerializerMixin, ModelViewSet):
            serializer_class = ProductSerializer        # 兜底
            list_serializer_class = ProductListSerializer
            retrieve_serializer_class = ProductDetailSerializer
            create_serializer_class = ProductCreateSerializer
            update_serializer_class = ProductUpdateSerializer

    DRF 的标准做法：
        list    → 列表页，字段少，加载快
        retrieve → 详情页，包含所有字段
        create  → 创建时，不需要 id
        update  → 更新时，需要 id
    """

    # 属性声明（可被子类覆盖）
    serializer_action_classes = None
    list_serializer_class = None
    retrieve_serializer_class = None
    create_serializer_class = None
    update_serializer_class = None
    partial_update_serializer_class = None
    destroy_serializer_class = None

    def get_serializer_class(self):
        """
        DRF 的 get_serializer_class() 决定用哪个序列化器。

        优先级：
            1. <action>_serializer_class  属性（如 list_serializer_class）
            2. serializer_action_classes  映射表（如 {'list': S1}）
            3. serializer_class           兜底

        DRF action 对应关系：
            GET    /items/         → list
            GET    /items/{id}/    → retrieve
            POST   /items/         → create
            PUT    /items/{id}/    → update
            PATCH  /items/{id}/    → partial_update
            DELETE /items/{id}/    → destroy
        """
        action = getattr(self, 'action', None)
        if not action:
            return super().get_serializer_class()

        # 1. 先找 <action>_serializer_class
        attr_name = f"{action}_serializer_class"
        specific = getattr(self, attr_name, None)
        if specific is not None:
            return specific

        # 2. 再找映射表
        mapping = getattr(self, 'serializer_action_classes', None) or {}
        if action in mapping:
            return mapping[action]

        # 3. 兜底
        return super().get_serializer_class()
