"""Role lifecycle and closed permission catalog."""
from django.db import transaction,IntegrityError
from apps.common.exceptions import BusinessError
from apps.rbac.models import Role,UserRole,RolePermission
from apps.rbac.permissions import require_permission,is_root,permission_codes,PERMISSIONS
from apps.audit import service as audit

class RoleService:
    def list_roles(self):
        roles=list(Role.objects.order_by('id'))
        for role in roles:role.user_count=UserRole.objects.filter(role=role,user__is_deleted=False).count()
        return roles
    def get_role_detail(self,role_id):return Role.objects.filter(pk=role_id).first()
    @staticmethod
    def _permissions(actor,codes):
        if not isinstance(codes,list) or len(codes)!=len(set(codes)) or any(x not in PERMISSIONS for x in codes):
            raise BusinessError(message='无效权限编码',code='INVALID_PERMISSIONS',status=400)
        if not set(codes)<=permission_codes(actor):raise BusinessError(message='不能授予超出自身权限',code='PERMISSION_DENIED',status=403)
    @staticmethod
    def _unique(data,role_id=None):
        for key in ('name','code'):
            if key in data and Role.objects.with_deleted().filter(**{key:data[key]}).exclude(pk=role_id).exists():
                raise BusinessError(message='角色名称或编码已使用（含已删除记录）',code='DUPLICATE_ROLE_'+key.upper(),status=409)
    @staticmethod
    def _set_permissions(role,codes):
        RolePermission.objects.with_deleted().filter(role=role).delete()
        RolePermission.objects.bulk_create([RolePermission(role=role,permission_code=code) for code in codes])
    @transaction.atomic
    def create_role(self,data,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'roles.write')
        from apps.rbac.serializers.role_serializers import RoleCreateSerializer
        serializer=RoleCreateSerializer(data=data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
        self._unique(data);codes=data.pop('permissions',[]);self._permissions(actor,codes)
        if data['code'] in ('root','boss','user'):raise BusinessError(message='保留系统角色编码',code='SYSTEM_ROLE_PROTECTED',status=403)
        try:
            with transaction.atomic():
                role=Role.objects.create(**data);self._set_permissions(role,codes);audit.record(actor,'role.create','role',role.pk)
        except IntegrityError as error:raise BusinessError(message='角色冲突',code='CONFLICT',status=409) from error
        return role
    @transaction.atomic
    def update_role(self,role_id,data,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'roles.write')
        role=Role.objects.select_for_update().filter(pk=role_id).first()
        if not role:raise BusinessError(message='角色不存在',code='ROLE_NOT_FOUND',status=404)
        from apps.rbac.serializers.role_serializers import RoleUpdateSerializer
        serializer=RoleUpdateSerializer(data=data);serializer.is_valid(raise_exception=True);data=serializer.validated_data
        if role.code in ('root','boss','user') and (('code' in data and data['code']!=role.code) or 'permissions' in data or ('is_unique' in data and data['is_unique']!=role.is_unique)):
            raise BusinessError(message='系统角色权限/编码/唯一性不可修改',code='SYSTEM_ROLE_PROTECTED',status=403)
        if not is_root(actor) and role.code in ('root','boss'):raise BusinessError(message='不能管理管理员角色',code='SYSTEM_ROLE_PROTECTED',status=403)
        if data.get('code') in ('root','boss','user') and data['code']!=role.code:raise BusinessError(message='保留系统角色编码',code='SYSTEM_ROLE_PROTECTED',status=403)
        current_codes=set(RolePermission.objects.filter(role=role).values_list('permission_code',flat=True)) & set(PERMISSIONS)
        if not is_root(actor) and not current_codes <= permission_codes(actor):
            raise BusinessError(message='不能修改超出自身权限的角色',code='PERMISSION_DENIED',status=403)
        self._unique(data,role.pk)
        if data.get('is_unique') and UserRole.objects.filter(role=role,user__is_deleted=False).count()>1:
            raise BusinessError(message='多人持有角色不能设为唯一',code='UNIQUE_ROLE_CONFLICT',status=409)
        codes=data.pop('permissions',None)
        if codes is not None:self._permissions(actor,codes)
        try:
            with transaction.atomic():
                for key,value in data.items():setattr(role,key,value)
                role.save()
                if codes is not None:self._set_permissions(role,codes)
                audit.record(actor,'role.update','role',role.pk)
        except IntegrityError as error:raise BusinessError(message='角色冲突',code='CONFLICT',status=409) from error
        return role
    @transaction.atomic
    def delete_role(self,role_id,*,actor=None):
        from apps.rbac.services.locking import reserve_lifecycle_write
        reserve_lifecycle_write()
        actor=require_permission(actor,'roles.write')
        role=Role.objects.select_for_update().filter(pk=role_id).first()
        if not role:raise BusinessError(message='角色不存在',code='ROLE_NOT_FOUND',status=404)
        if role.code in ('root','user','boss'):raise BusinessError(message='系统角色不可删除',code='SYSTEM_ROLE_PROTECTED',status=403)
        if UserRole.objects.filter(role=role,user__is_deleted=False).exists():raise BusinessError(message='角色仍有用户，请先解绑',code='ROLE_IN_USE',status=409)
        role.soft_delete();RolePermission.objects.with_deleted().filter(role=role).delete();audit.record(actor,'role.delete','role',role.pk)
    @staticmethod
    def enforce_unique_role(user_id,role_ids):
        for role in Role.objects.select_for_update().filter(pk__in=role_ids,is_unique=True):
            if UserRole.objects.filter(role=role,user__is_deleted=False).exclude(user_id=user_id).exists():
                raise BusinessError(message='唯一角色已有持有人',code='UNIQUE_ROLE_CONFLICT',status=409)
