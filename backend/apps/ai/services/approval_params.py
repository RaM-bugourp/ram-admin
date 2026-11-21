"""Operation-specific parameter boundary. Never persist or expose raw passwords."""
from django.contrib.auth.hashers import make_password
from rest_framework.exceptions import ValidationError
from apps.rbac.serializers.user_serializers import UserCreateSerializer,UserUpdateSerializer

SAFE_FIELDS={'create_user':{'username','email','is_active','role_ids'},'update_user':{'user_id','username','email','is_active','role_ids'},'delete_user':{'user_id'},'assign_roles':{'user_id','role_ids'}}

def prepare(operation,params):
    if operation not in SAFE_FIELDS or not isinstance(params,dict): raise ValidationError('无效操作参数')
    data=dict(params)
    allowed=SAFE_FIELDS[operation]|({'password'} if operation=='create_user' else set())|({'id'} if operation!='create_user' else set())
    if set(data)-allowed: raise ValidationError('包含不支持的操作字段')
    if operation=='create_user':
        serializer=UserCreateSerializer(data=data);serializer.is_valid(raise_exception=True);result=dict(serializer.validated_data)
        from apps.rbac.services.user_service import validate_roles
        validate_roles(result.get('role_ids',[]));result['password_digest']=make_password(result.pop('password'));return result
    user_id=data.pop('user_id',data.pop('id',None))
    if type(user_id) is not int or user_id<=0: raise ValidationError('user_id必须为正整数')
    if operation=='delete_user': return {'user_id':user_id}
    serializer=UserUpdateSerializer(data=data);serializer.is_valid(raise_exception=True);result=dict(serializer.validated_data)
    if 'role_ids' in result:
        from apps.rbac.services.user_service import validate_roles
        validate_roles(result['role_ids'])
    if operation=='assign_roles' and 'role_ids' not in result: raise ValidationError('缺少role_ids')
    return {'user_id':user_id,**result}

def safe_params(operation,params):
    # Fixed scalar/list fields; never echo unknown/nested/free-form values from old rows.
    result={}
    if isinstance(params,dict):
        for key in SAFE_FIELDS.get(operation,set()):
            value=params.get(key)
            if key=='role_ids':
                if isinstance(value,list) and all(type(x) is int for x in value): result[key]=value
            elif key in ('username','email'):
                if isinstance(value,str): result[key]=value[:150]
            elif key=='is_active' and type(value) is bool: result[key]=value
            elif key=='user_id' and type(value) is int: result[key]=value
    if operation=='create_user': result['password']='[REDACTED]'
    return result
