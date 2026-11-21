"""Session authentication, current capabilities and self-service settings."""
from django.contrib.auth import authenticate,login,logout,update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authentication import CSRFCheck
from rest_framework.exceptions import PermissionDenied,ValidationError
from apps.common.exceptions import BusinessError
from apps.rbac.permissions import EffectiveAuthenticated,permission_codes
from apps.audit import service as audit

def user_data(user):
    from apps.rbac.models import UserRole
    roles=[{'id':row.role_id,'name':row.role.name,'code':row.role.code} for row in UserRole.objects.select_related('role').filter(user=user,role__is_deleted=False)]
    return {'id':user.pk,'username':user.username,'email':user.email,'is_superuser':user.is_superuser,'roles':roles,'permissions':sorted(permission_codes(user))}

class AuthViewSet(viewsets.GenericViewSet):
    def get_permissions(self):
        return [AllowAny()] if self.action in ('login','csrf_token') else [EffectiveAuthenticated()]
    @action(detail=False,methods=['get'],url_path='csrf')
    def csrf_token(self,request):
        from django.middleware.csrf import get_token
        return Response({'data':{'csrf_token':get_token(request)}})
    @action(detail=False,methods=['post'])
    def login(self,request):
        # DRF's anonymous SessionAuthentication skips CSRF: enforce explicitly here.
        check=CSRFCheck(lambda req:None);check.process_request(request)
        if check.process_view(request,None,(),{}):raise PermissionDenied('CSRF验证失败',code='csrf_failed')
        username=request.data.get('username','');password=request.data.get('password','')
        if not isinstance(username,str) or not isinstance(password,str) or not username.strip() or not password:
            raise BusinessError('用户名和密码不能为空','INVALID_CREDENTIALS',400)
        from apps.rbac import security
        if len(username)>150 or len(password)>4096:raise BusinessError('用户名或密码错误','INVALID_CREDENTIALS',401)
        reservation=security.reserve_login(username,request.META.get('REMOTE_ADDR',''))
        if reservation.get('unavailable'):raise security.unavailable()
        if reservation.get('retry_after'):
            request._login_event_recorded=True
            return Response({'error':{'code':'LOGIN_LIMITED','message':'登录尝试过多，请稍后重试'}},status=429,headers={'Retry-After':str(reservation['retry_after'])})
        user=authenticate(request,username=username.strip(),password=password)
        if user is None or not user.is_active:
            try:security.failed_login()
            except Exception:raise security.unavailable() from None
            request._login_event_recorded=True
            raise BusinessError('用户名或密码错误','INVALID_CREDENTIALS',401)
        # Audit first: an unavailable audit cannot establish a successful new login.
        try:
            with transaction.atomic():
                audit.record(user,'session.login','session')
                login(request,user)
                request.session.save()
                security.register_session(user,request.session.session_key)
                security.complete_login(reservation['account_key'])
        except Exception:
            logout(request)
            raise security.unavailable() from None
        return Response({'data':user_data(user)})
    @action(detail=False,methods=['get'],url_path='sessions')
    def sessions(self,request):
        from apps.rbac.security import list_sessions
        if request.query_params:raise ValidationError('不支持的查询字段')
        return Response({'data':list_sessions(request.user,request.session.session_key)})
    @action(detail=False,methods=['post'],url_path='revoke-session')
    def revoke_session(self,request):
        import uuid
        from apps.rbac.security import revoke_sessions
        if set(request.data)!={'id'}:raise ValidationError('仅接受会话句柄id')
        try:handle=uuid.UUID(str(request.data['id']))
        except (ValueError,TypeError,AttributeError):raise ValidationError('会话句柄格式不正确')
        result=revoke_sessions(request.user,request.session.session_key,handle=handle)
        if result['current_revoked']:logout(request)
        return Response({'data':result})
    @action(detail=False,methods=['post'],url_path='revoke-other-sessions')
    def revoke_other_sessions(self,request):
        from apps.rbac.security import revoke_sessions
        if request.data:raise ValidationError('不接受目标用户字段')
        return Response({'data':revoke_sessions(request.user,request.session.session_key,others=True)})
    @action(detail=False,methods=['post'],url_path='revoke-user-sessions')
    def revoke_user_sessions(self,request):
        from apps.common.inputs import positive_int
        from apps.rbac.security import revoke_sessions
        if set(request.data)!={'user_id'}:raise ValidationError('仅接受user_id')
        result=revoke_sessions(request.user,request.session.session_key,target_id=positive_int(request.data['user_id'],'user_id'))
        if result['current_revoked']:logout(request)
        return Response({'data':result})
    @action(detail=False,methods=['post'])
    def logout(self,request):
        audit.record(request.user,'session.logout','session');logout(request);return Response({'data':{}})
    @action(detail=False,methods=['get'],url_path='user-info')
    def user_info(self,request):return Response({'data':user_data(request.user)})
    @action(detail=False,methods=['get'],url_path='settings')
    def account_settings(self,request):
        from django.conf import settings
        return Response({'data':{'username':request.user.username,'email':request.user.email,'ai_optional':True,'ai_enabled':bool(getattr(settings,'AI_UI_ENABLED',False)),'password_min_length':8}})
    @action(detail=False,methods=['post'],url_path='change-password')
    @transaction.atomic
    def change_password(self,request):
        from apps.rbac.models import User
        user=User.objects.select_for_update().get(pk=request.user.pk)
        if set(request.data)-{'old_password','new_password'}:raise ValidationError('不支持的字段')
        old=request.data.get('old_password');new=request.data.get('new_password')
        if not isinstance(old,str) or not user.check_password(old):raise BusinessError('原密码错误','INVALID_PASSWORD',400)
        if not isinstance(new,str):raise ValidationError('新密码格式不正确')
        try:validate_password(new,user)
        except DjangoValidationError as error:raise ValidationError({'new_password':list(error.messages)})
        user.set_password(new);user.save(update_fields=['password_hash']);audit.record(user,'user.change_password','user',user.pk)
        update_session_auth_hash(request,user)
        return Response({'data':{'message':'密码修改成功，其他会话已失效'}})
