"""Effective RBAC identities. Unknown actions and missing actors fail closed."""
from rest_framework.permissions import BasePermission, SAFE_METHODS
from apps.common.exceptions import BusinessError

PERMISSIONS = {
    'dashboard.read': '工作台', 'users.read': '查看用户', 'users.write': '管理用户',
    'roles.read': '查看角色', 'roles.write': '管理角色', 'audit.read': '查看操作审计',
}
BOSS_PERMISSIONS = {'dashboard.read','users.read','users.write','roles.read'}

def effective_user(user):
    if not user or not getattr(user,'pk',None): return None
    from apps.rbac.models import User
    return User.objects.filter(pk=user.pk,is_active=True).first()

def has_role(user, code):
    user=effective_user(user)
    if not user: return False
    from apps.rbac.models import UserRole
    return UserRole.objects.filter(user=user,role__code=code,role__is_deleted=False).exists()

def is_root(user):
    current=effective_user(user)
    return bool(current and (current.is_superuser or has_role(current,'root')))

def permission_codes(user):
    user=effective_user(user)
    if not user: return set()
    if is_root(user): return set(PERMISSIONS)
    if has_role(user,'boss'): return set(BOSS_PERMISSIONS)
    from apps.rbac.models import RolePermission
    codes=RolePermission.objects.filter(role__is_deleted=False,role__userrole__user=user,role__userrole__is_deleted=False).values_list('permission_code',flat=True)
    return {'dashboard.read'} | (set(codes)&set(PERMISSIONS))

def require_permission(actor, code):
    current=effective_user(actor)
    if not current or code not in permission_codes(current):
        raise BusinessError(message='无权执行此操作',code='PERMISSION_DENIED',status=403)
    return current

def boss_can_manage_user(actor,target):
    if not effective_user(actor): return False
    if is_root(actor): return True
    from apps.rbac.models import UserRole
    # Target privilege survives disable: otherwise reset-password + reactivate takes it over.
    target_admin = bool(target and (target.is_superuser or UserRole.objects.filter(user_id=target.pk, role__code__in={'root','boss'}, role__is_deleted=False).exists()))
    if target_admin: return False
    from apps.rbac.models import RolePermission
    target_codes = set(RolePermission.objects.filter(role__is_deleted=False, role__userrole__user_id=target.pk, role__userrole__is_deleted=False).values_list('permission_code', flat=True)) & set(PERMISSIONS)
    actor_codes = permission_codes(actor)
    return 'users.write' in actor_codes and target_codes <= actor_codes

def boss_can_assign_roles(actor,role_ids):
    if not effective_user(actor): return False
    if is_root(actor): return True
    from apps.rbac.models import Role,RolePermission
    roles=Role.objects.filter(id__in=list(role_ids or []))
    if roles.filter(code__in={'root','boss'}).exists(): return False
    requested=set(RolePermission.objects.filter(role__in=roles).values_list('permission_code',flat=True))
    return 'users.write' in permission_codes(actor) and requested<=permission_codes(actor)

class IsAdminOrReadOnly(BasePermission):
    """Compatibility name; actual resource/action permission is explicit."""
    message='无权访问此管理功能'
    def has_permission(self,request,view):
        resource=getattr(view,'permission_resource','')
        suffix='read' if request.method in SAFE_METHODS else 'write'
        return bool(resource and f'{resource}.{suffix}' in permission_codes(request.user))

class EffectiveAuthenticated(BasePermission):
    def has_permission(self,request,view): return effective_user(request.user) is not None
