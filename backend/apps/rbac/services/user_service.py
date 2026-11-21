"""Core user management. Every mutation requires a current explicit actor."""
from django.core.paginator import Paginator
from django.db import transaction,IntegrityError
from django.db.models import Q
from apps.common.exceptions import BusinessError
from apps.rbac.models import User,UserRole,Role
from apps.rbac.permissions import require_permission,boss_can_manage_user,boss_can_assign_roles,is_root
from apps.audit import service as audit

def validate_roles(role_ids):
    if not isinstance(role_ids,list) or any(type(x) is not int or x<=0 for x in role_ids) or len(role_ids)!=len(set(role_ids)):
        raise BusinessError(message='角色ID必须为不重复的正整数',code='INVALID_ROLES',status=400)
    if Role.objects.filter(pk__in=role_ids).count()!=len(role_ids):
        raise BusinessError(message='角色不存在或已删除',code='INVALID_ROLES',status=400)
    return role_ids

def protect_last_root(user,data=None,deleting=False):
    data=data or {}
    if not is_root(user): return
    keeps_active=not deleting and data.get('is_active',user.is_active)
    keeps_root=user.is_superuser or ('role_ids' not in data and is_root(user)) or Role.objects.filter(pk__in=data.get('role_ids',[]),code='root').exists()
    if keeps_active and keeps_root: return
    # Lock all effective candidates before deciding. SQLite serializes writes; cross-engine
    # stress/serializable guarantees remain a separately declared verification boundary.
    candidates=list(User.objects.select_for_update().filter(is_active=True).exclude(pk=user.pk))
    if not any(is_root(candidate) for candidate in candidates):
        raise BusinessError(message='至少保留一个有效root',code='LAST_ROOT_PROTECTED',status=409)

class UserService:
    def list_users(self,page=1,page_size=20,search=''):
        qs=User.objects.order_by('-created_at','-id')
        if search: qs=qs.filter(Q(username__icontains=search)|Q(email__icontains=search))
        paginator=Paginator(qs,page_size); obj=paginator.get_page(page)
        return {'items':list(obj.object_list),'page':obj.number,'page_size':page_size,'total':paginator.count,'total_pages':paginator.num_pages}
    def get_user_detail(self,user_id): return User.objects.filter(pk=user_id).first()
    @staticmethod
    def _assignment(actor,ids):
        validate_roles(ids)
        if not boss_can_assign_roles(actor,ids):
            raise BusinessError(message='不能授予管理员或超出自身的权限',code='ADMIN_ROLE_PROTECTED',status=403)
    @staticmethod
    def _target(user_id,actor):
        user=User.objects.select_for_update().filter(pk=user_id).first()
        if not user: raise BusinessError(message='用户不存在',code='USER_NOT_FOUND',status=404)
        if not boss_can_manage_user(actor,user):
            raise BusinessError(message='不能管理管理员账号',code='ADMIN_TARGET_PROTECTED',status=403)
        return user
    @staticmethod
    def _unique(data,user_id=None):
        for key,code in [('username','DUPLICATE_USERNAME'),('email','DUPLICATE_EMAIL')]:
            if key in data and User.objects.with_deleted().filter(**{key:data[key]}).exclude(pk=user_id).exists():
                raise BusinessError(message='用户名或邮箱已被使用（含已删除记录）',code=code,status=409)
    @staticmethod
    def _roles(user,ids):
        from apps.rbac.services.role_service import RoleService
        RoleService.enforce_unique_role(user.pk,ids)
        UserRole.objects.with_deleted().filter(user=user).delete()
        UserRole.objects.bulk_create([UserRole(user=user,role_id=rid) for rid in ids])
    @transaction.atomic
    def create_user(self,data,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'users.write')
        from apps.rbac.serializers.user_serializers import UserCreateSerializer
        serializer=UserCreateSerializer(data=data); serializer.is_valid(raise_exception=True); data=serializer.validated_data
        self._assignment(actor,data.get('role_ids',[])); self._unique(data)
        try:
            with transaction.atomic():
                user=User.objects.create_user(username=data['username'],email=data['email'],password=data['password'],is_active=data.get('is_active',True))
                self._roles(user,data.get('role_ids',[])); audit.record(actor,'user.create','user',user.pk)
        except IntegrityError as error:
            raise BusinessError(message='用户或关联已存在',code='CONFLICT',status=409) from error
        return user
    @transaction.atomic
    def update_user(self,user_id,data,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'users.write'); user=self._target(user_id,actor)
        from apps.rbac.serializers.user_serializers import UserUpdateSerializer
        serializer=UserUpdateSerializer(data=data); serializer.is_valid(raise_exception=True); data=serializer.validated_data
        self._unique(data,user.pk)
        if 'role_ids' in data: self._assignment(actor,data['role_ids'])
        protect_last_root(user,data)
        try:
            with transaction.atomic():
                for field in ('username','email','is_active'):
                    if field in data: setattr(user,field,data[field])
                user.save()
                if 'role_ids' in data: self._roles(user,data['role_ids'])
                audit.record(actor,'user.update','user',user.pk)
        except IntegrityError as error:
            raise BusinessError(message='用户或关联已存在',code='CONFLICT',status=409) from error
        return user
    @transaction.atomic
    def delete_user(self,user_id,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'users.write'); user=self._target(user_id,actor); protect_last_root(user,deleting=True)
        UserRole.objects.with_deleted().filter(user=user).delete(); user.soft_delete(); audit.record(actor,'user.delete','user',user.pk)
    @transaction.atomic
    def reset_password(self,user_id,new_password,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'users.write'); user=self._target(user_id,actor)
        from apps.rbac.serializers.user_serializers import UserResetPasswordSerializer
        serializer=UserResetPasswordSerializer(data={'password':new_password});serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['password']);user.save(update_fields=['password_hash']);audit.record(actor,'user.reset_password','user',user.pk)
    @transaction.atomic
    def create_from_approval(self,approval,*,actor=None):
        """Private approval capability: persisted approved row bound to current root reviewer."""
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'users.write')
        from apps.ai.models import AIApproval
        from django.contrib.auth.hashers import identify_hasher
        current=AIApproval.objects.select_for_update().filter(pk=approval.pk,status='approved',approved_by=actor,operation='create_user').first()
        if not is_root(actor) or not current: raise BusinessError(message='无效审批执行上下文',code='PERMISSION_DENIED',status=403)
        data=dict(current.params);digest=data.pop('password_digest',None)
        if not digest: raise BusinessError(message='审批缺少安全密码摘要',code='INVALID_APPROVAL',status=400)
        identify_hasher(digest)
        self._assignment(actor,data.get('role_ids',[]));self._unique(data)
        # create_user accepts raw passwords only. Do not route a hash through it.
        user=User.objects.create_user(username=data['username'],email=data['email'],password=None,is_active=data.get('is_active',True))
        user.password_hash=digest;user.save(update_fields=['password_hash']);self._roles(user,data.get('role_ids',[]));audit.record(actor,'user.create','user',user.pk)
        return user
