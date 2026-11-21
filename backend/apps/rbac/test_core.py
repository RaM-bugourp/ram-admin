from unittest.mock import patch
from django.test import TestCase,override_settings
from rest_framework.test import APIClient
from apps.rbac.models import User,Role,UserRole,RolePermission
from apps.audit.models import OperationLog
from apps.rbac.services.user_service import UserService
from apps.rbac.services.role_service import RoleService
from apps.common.exceptions import BusinessError
from apps.ai.permissions import AgentTokenService
from apps.ai.models import AIApproval,AIApprovalLog

class CoreManagementTests(TestCase):
 def setUp(self):
  self.root=User.objects.create_user('root-core','r@core.invalid','Synthetic-Only-845!',is_superuser=True)
  self.user=User.objects.create_user('user-core','u@core.invalid','Synthetic-Only-845!')
  self.role=Role.objects.create(name='ordinary-role',code='ordinary_role')
  self.c=APIClient();self.c.force_authenticate(self.root)
 def test_ordinary_management_default_denied(self):
  c=APIClient();c.force_authenticate(self.user)
  for path in ['/api/rbac/users/','/api/rbac/roles/','/api/audit/logs/']:
   self.assertEqual(c.get(path).status_code,403)
 def test_explicit_read_permissions_real_audit(self):
  UserRole.objects.create(user=self.user,role=self.role);RolePermission.objects.create(role=self.role,permission_code='audit.read')
  OperationLog.objects.create(actor=self.root,action='user.create',resource='user',object_id='12')
  c=APIClient();c.force_authenticate(self.user);r=c.get('/api/audit/logs/?resource=user&page_size=1')
  self.assertEqual(r.status_code,200);self.assertEqual(r.data['pagination']['total'],1)
  self.assertEqual(set(r.data['data'][0]),{'id','actor_id','actor_name','action','resource','object_id','outcome','created_at'})
  self.assertEqual(c.post('/api/rbac/users/',{},format='json').status_code,403)
 def test_invalid_resource_ids_and_unknown_privilege_fields(self):
  for path in ['/api/rbac/users/not-a-number/','/api/rbac/roles/not-a-number/','/api/ai/approval/not-a-number/']:
   self.assertEqual(self.c.get(path).status_code,400)
  self.assertEqual(self.c.put(f'/api/rbac/users/{self.user.pk}/',{'is_superuser':True},format='json').status_code,400)
  self.user.refresh_from_db();self.assertFalse(self.user.is_superuser)

 def test_invalid_pagination_is_structured_400(self):
  for path in ['/api/rbac/users/','/api/audit/logs/']:
   for value in ['abc','0','-1','101']:
    self.assertEqual(self.c.get(path+'?page_size='+value).status_code,400)
 def test_invalid_role_ids_no_partial_user(self):
  dead=Role.objects.create(name='dead-role',code='dead_role');dead.soft_delete()
  for roles in [[self.role.pk,self.role.pk],[999999],[dead.pk]]:
   r=self.c.post('/api/rbac/users/',{'username':'bad-user','email':'bad@core.invalid','password':'Synthetic-Only-845!','role_ids':roles},format='json')
   self.assertEqual(r.status_code,400);self.assertFalse(User.objects.filter(username='bad-user').exists())
 def test_tombstone_unique_conflicts_not_500(self):
  self.user.soft_delete()
  r=self.c.post('/api/rbac/users/',{'username':self.user.username,'email':self.user.email,'password':'Synthetic-Only-845!'},format='json');self.assertEqual(r.status_code,409)
  self.role.soft_delete();self.assertEqual(self.c.post('/api/rbac/roles/',{'name':self.role.name,'code':self.role.code},format='json').status_code,409)
 def test_delete_user_releases_unique_role(self):
  self.role.is_unique=True;self.role.save();UserRole.objects.create(user=self.user,role=self.role)
  UserService().delete_user(self.user.pk,actor=self.root);self.assertFalse(UserRole.objects.with_deleted().filter(user=self.user).exists())
  created=UserService().create_user({'username':'replacement','email':'rep@core.invalid','password':'Synthetic-Only-845!','role_ids':[self.role.pk]},actor=self.root);self.assertTrue(UserRole.objects.filter(user=created).exists())
 def test_unique_switch_and_assigned_role_delete_rejected(self):
  UserRole.objects.create(user=self.user,role=self.role);UserRole.objects.create(user=self.root,role=self.role)
  self.assertEqual(self.c.put(f'/api/rbac/roles/{self.role.pk}/',{'is_unique':True},format='json').status_code,409)
  self.assertEqual(self.c.delete(f'/api/rbac/roles/{self.role.pk}/').status_code,409)
 def test_last_root_disable_delete_blocked_and_other_root_allows(self):
  for method,data in [('put',{'is_active':False}),('delete',None)]:
   self.assertEqual(getattr(self.c,method)(f'/api/rbac/users/{self.root.pk}/',data,format='json').status_code,409)
  role=Role.objects.create(name='root-role',code='root');UserRole.objects.create(user=self.user,role=role)
  self.assertEqual(self.c.put(f'/api/rbac/users/{self.root.pk}/',{'is_active':False},format='json').status_code,200)
 def test_last_role_root_unlink_blocked(self):
  self.root.is_superuser=False;self.root.save();role=Role.objects.create(name='root-role',code='root');UserRole.objects.create(user=self.root,role=role)
  self.assertEqual(self.c.put(f'/api/rbac/users/{self.root.pk}/',{'role_ids':[]},format='json').status_code,409)
 def test_audit_failure_rolls_back_success_mutation(self):
  with patch('apps.audit.service.record',side_effect=RuntimeError('synthetic failure')):
   with self.assertRaises(RuntimeError):UserService().update_user(self.user.pk,{'email':'changed@core.invalid'},actor=self.root)
  self.user.refresh_from_db();self.assertEqual(self.user.email,'u@core.invalid')
 def test_role_none_actor_and_unknown_permissions_rejected(self):
  with self.assertRaises(BusinessError):RoleService().create_role({'name':'new-role','code':'new_role'})
  self.assertEqual(self.c.post('/api/rbac/roles/',{'name':'new-role','code':'new_role','permissions':['anything.root']},format='json').status_code,400)
 def test_disabled_admin_targets_still_protected_from_takeover(self):
  boss_role=Role.objects.create(name='boss',code='boss');root_role=Role.objects.create(name='root',code='root')
  boss=User.objects.create_user('boss-writer','boss@core.invalid',None);UserRole.objects.create(user=boss,role=boss_role)
  UserRole.objects.create(user=self.user,role=self.role);RolePermission.objects.create(role=self.role,permission_code='users.write')
  targets=[User.objects.create_user('disabled-super','ds@core.invalid','Original-Only-987!',is_active=False,is_superuser=True)]
  for code,role in [('root',root_role),('boss',boss_role)]:
   target=User.objects.create_user('disabled-'+code,code+'@disabled.invalid','Original-Only-987!',is_active=False);UserRole.objects.create(user=target,role=role);targets.append(target)
  for actor in [boss,self.user]:
   client=APIClient();client.force_authenticate(actor)
   for target in targets:
    for method,path,data in [('post',f'/api/rbac/users/{target.pk}/reset-password/',{'password':'Attacker-Only-987!'}),('put',f'/api/rbac/users/{target.pk}/',{'is_active':True}),('delete',f'/api/rbac/users/{target.pk}/',None)]:
     self.assertEqual(getattr(client,method)(path,data,format='json').status_code,403)
    target.refresh_from_db();self.assertFalse(target.is_active);self.assertTrue(target.check_password('Original-Only-987!'))
  inactive=User.objects.create_user('disabled-normal','dn@core.invalid',None,is_active=False)
  self.assertEqual(client.put(f'/api/rbac/users/{inactive.pk}/',{'is_active':True},format='json').status_code,200)

 def test_writer_cannot_take_over_higher_custom_permission_target(self):
  UserRole.objects.create(user=self.user,role=self.role);RolePermission.objects.create(role=self.role,permission_code='users.write')
  high=Role.objects.create(name='high-custom',code='high_custom');RolePermission.objects.create(role=high,permission_code='audit.read')
  for active in [True,False]:
   target=User.objects.create_user('high-'+str(active),str(active)+'@high.invalid','Original-Only-987!',is_active=active);UserRole.objects.create(user=target,role=high)
   c=APIClient();c.force_authenticate(self.user)
   self.assertEqual(c.post(f'/api/rbac/users/{target.pk}/reset-password/',{'password':'Takeover-Only-987!'},format='json').status_code,403)
   self.assertEqual(c.put(f'/api/rbac/users/{target.pk}/',{'is_active':True},format='json').status_code,403)
   self.assertEqual(c.delete(f'/api/rbac/users/{target.pk}/').status_code,403)
   target.refresh_from_db();self.assertTrue(target.check_password('Original-Only-987!'))

 def test_boss_and_service_cannot_strip_higher_authority_targets(self):
  boss_role=Role.objects.create(name='boss',code='boss');boss=User.objects.create_user('boss-actor','bossactor@core.invalid',None);UserRole.objects.create(user=boss,role=boss_role)
  for code in ['audit.read','roles.write']:
   role=Role.objects.create(name=code,code=code.replace('.','_'));RolePermission.objects.create(role=role,permission_code=code)
   for active in [True,False]:
    target=User.objects.create_user(code+str(active),code+str(active)+'@target.invalid','Original-Only-987!',is_active=active);UserRole.objects.create(user=target,role=role)
    with self.assertRaises(BusinessError):UserService().update_user(target.pk,{'role_ids':[],'is_active':True},actor=boss)
    with self.assertRaises(BusinessError):UserService().reset_password(target.pk,'Takeover-Only-987!',actor=boss)
    with self.assertRaises(BusinessError):UserService().delete_user(target.pk,actor=boss)
    target.refresh_from_db();self.assertEqual(target.is_active,active);self.assertFalse(target.is_deleted);self.assertTrue(UserRole.objects.filter(user=target,role=role).exists());self.assertTrue(target.check_password('Original-Only-987!'))
    UserService().reset_password(target.pk,'Root-Authorized-987!',actor=self.root);target.refresh_from_db();self.assertTrue(target.check_password('Root-Authorized-987!'))
  UserService().reset_password(self.user.pk,'Boss-Authorized-987!',actor=boss);self.user.refresh_from_db();self.assertTrue(self.user.check_password('Boss-Authorized-987!'))

 def test_lower_role_editor_cannot_strip_higher_role(self):
  UserRole.objects.create(user=self.user,role=self.role)
  for code in ['roles.write','users.write']:RolePermission.objects.create(role=self.role,permission_code=code)
  high=Role.objects.create(name='audit-high',code='audit_high');RolePermission.objects.create(role=high,permission_code='audit.read')
  with self.assertRaises(BusinessError):RoleService().update_role(high.pk,{'permissions':[]},actor=self.user)
  self.assertTrue(RolePermission.objects.filter(role=high,permission_code='audit.read').exists())

 def test_custom_writer_cannot_promote_or_manage_admin(self):
  UserRole.objects.create(user=self.user,role=self.role);RolePermission.objects.create(role=self.role,permission_code='users.write')
  c=APIClient();c.force_authenticate(self.user)
  self.assertEqual(c.put(f'/api/rbac/users/{self.root.pk}/',{'is_active':False},format='json').status_code,403)
  promoted=Role.objects.create(name='privileged-role',code='privileged_role');RolePermission.objects.create(role=promoted,permission_code='roles.write')
  self.assertEqual(c.put(f'/api/rbac/users/{self.user.pk}/',{'role_ids':[promoted.pk]},format='json').status_code,403)

class CoreSessionTests(TestCase):
 def setUp(self):self.user=User.objects.create_user('session-user','session@core.invalid','Synthetic-Only-845!')
 def login_client(self):
  c=APIClient(enforce_csrf_checks=True);c.get('/api/auth/csrf/');c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)
  self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':'Synthetic-Only-845!'},format='json').status_code,200)
  c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value);return c
 def test_login_csrf_missing_wrong_and_origin_denied(self):
  for header in [{},{'HTTP_X_CSRFTOKEN':'x'*32},{'HTTP_ORIGIN':'https://evil.invalid'}]:
   c=APIClient(enforce_csrf_checks=True);c.get('/api/auth/csrf/');self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':'Synthetic-Only-845!'},format='json',**header).status_code,403)
 def test_login_valid_csrf_token_foreign_origin_denied(self):
  c=APIClient(enforce_csrf_checks=True);c.get('/api/auth/csrf/');token=c.cookies['csrftoken'].value
  response=c.post('/api/auth/login/',{'username':self.user.username,'password':'Synthetic-Only-845!'},format='json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='https://evil.invalid')
  self.assertEqual(response.status_code,403);self.assertNotIn('sessionid',c.cookies)

 def test_password_change_keeps_current_revokes_other_session(self):
  first=self.login_client();second=self.login_client()
  r=first.post('/api/auth/change-password/',{'old_password':'Synthetic-Only-845!','new_password':'Updated-Only-987!'},format='json');self.assertEqual(r.status_code,200)
  self.assertEqual(first.get('/api/auth/user-info/').status_code,200);self.assertEqual(second.get('/api/auth/user-info/').status_code,403)
 def test_password_wrong_old_and_target_id_no_change(self):
  c=self.login_client()
  for data in [{'old_password':'bad','new_password':'Updated-Only-987!'},{'old_password':'Synthetic-Only-845!','new_password':'Updated-Only-987!','user_id':123}]:self.assertEqual(c.post('/api/auth/change-password/',data,format='json').status_code,400)
  self.user.refresh_from_db();self.assertTrue(self.user.check_password('Synthetic-Only-845!'))
 def test_disabled_and_deleted_session_rejected(self):
  c=self.login_client();self.user.is_active=False;self.user.save();self.assertEqual(c.get('/api/auth/user-info/').status_code,403)
  self.user.is_active=True;self.user.save();c=self.login_client();self.user.soft_delete();self.assertEqual(c.get('/api/auth/user-info/').status_code,403)
 def test_login_valid_token_same_origin_succeeds(self):
  c=APIClient(enforce_csrf_checks=True);c.get('/api/auth/csrf/');token=c.cookies['csrftoken'].value
  self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':'Synthetic-Only-845!'},format='json',HTTP_X_CSRFTOKEN=token,HTTP_ORIGIN='http://testserver').status_code,200)

@override_settings(AI_APPROVAL_AUTO_EXECUTE=True)
class ApprovalExecutionTests(TestCase):
 def setUp(self):
  self.root=User.objects.create_user('approval-root','approval@core.invalid','Synthetic-Only-845!',is_superuser=True);self.c=APIClient();self.c.force_authenticate(self.root)
 def submit(self,params=None):
  return self.c.post('/api/ai/approval/submit/',{'agent_id':'synthetic','operation':'create_user','params':params or {'username':'approved-user','email':'approved@core.invalid','password':'Private-Only-987!'}},format='json')
 def test_execute_hash_once_and_duplicate_review_denied(self):
  r=self.submit();self.assertEqual(r.status_code,201);pk=r.data['data']['id']
  self.assertEqual(self.c.post(f'/api/ai/approval/{pk}/review/',{'action':'approve'},format='json').data['data']['status'],'executed')
  self.assertTrue(User.objects.get(username='approved-user').check_password('Private-Only-987!'));self.assertNotIn('password_digest',AIApproval.objects.get(pk=pk).params)
  self.assertEqual(self.c.post(f'/api/ai/approval/{pk}/review/',{'action':'approve'},format='json').status_code,409)
 def test_external_hash_fields_rejected_and_encoded_password_is_literal(self):
  for key in ['password_digest','password_hash','encoded']:
   self.assertEqual(self.submit({'username':'injected','email':'injected@core.invalid','password':'Private-Only-987!',key:'md5$bad'}).status_code,400)
  literal='md5$looks$likeahash';r=self.submit({'username':'literal-user','email':'literal@core.invalid','password':literal});pk=r.data['data']['id']
  self.c.post(f'/api/ai/approval/{pk}/review/',{'action':'approve'},format='json');self.assertTrue(User.objects.get(username='literal-user').check_password(literal))
 def test_failure_rolls_back_business_and_records_safe_failure(self):
  pk=self.submit().data['data']['id']
  with patch('apps.audit.service.record',side_effect=RuntimeError('Private-Only-987!')):r=self.c.post(f'/api/ai/approval/{pk}/review/',{'action':'approve'},format='json')
  self.assertEqual(r.status_code,200);self.assertEqual(r.data['data']['status'],'failed');self.assertFalse(User.objects.filter(username='approved-user').exists());self.assertNotIn('Private-Only-987!',str(r.data))
 def test_legacy_unknown_and_nested_params_not_exposed(self):
  row=AIApproval.objects.create(agent_id='legacy',operation='create_user',params={'password':'secret-marker','nested':{'token':'secret-marker'}},reason='secret-marker')
  r=self.c.get(f'/api/ai/approval/{row.pk}/');self.assertEqual(r.data['data']['attribution'],'unknown-legacy');self.assertNotIn('secret-marker',str(r.data))
