import uuid
from unittest.mock import patch
from django.test import TestCase
from django.utils import timezone
from django.contrib.sessions.models import Session
from rest_framework.test import APIClient
from apps.rbac.models import User, Role, UserRole, RolePermission, LoginWindow, ManagedSession
from apps.rbac import security
from apps.rbac.backends import UserBackend
from apps.audit.models import OperationLog
from apps.common.exceptions import BusinessError

PASSWORD = 'Synthetic-Only-845!'

class SecurityOpsTests(TestCase):
    def setUp(self):
        self.root=User.objects.create_user('security-root','r@security.invalid',PASSWORD,is_superuser=True)
        self.user=User.objects.create_user('security-user','u@security.invalid',PASSWORD)
    def csrf_client(self):
        c=APIClient(enforce_csrf_checks=True);c.get('/api/auth/csrf/');c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value);return c
    def login(self,user=None):
        c=self.csrf_client();self.assertEqual(c.post('/api/auth/login/',{'username':(user or self.user).username,'password':PASSWORD},format='json').status_code,200);c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value);return c
    def test_unknown_wrong_inactive_same_response_and_anonymous_event(self):
        inactive=User.objects.create_user('inactive-security','i@security.invalid',PASSWORD,is_active=False)
        outputs=[]
        for name,pw in [('unknown-security',PASSWORD),(self.user.username,'wrong-password'),(inactive.username,PASSWORD)]:
            c=self.csrf_client();r=c.post('/api/auth/login/',{'username':name,'password':pw},format='json');self.assertEqual(r.status_code,401);outputs.append(r.data)
        self.assertEqual(outputs[0],outputs[1]);self.assertEqual(outputs[1],outputs[2])
        events=OperationLog.objects.all();self.assertEqual(events.count(),3);self.assertEqual(set(events.values_list('action',flat=True)),{'session.login_failed'});self.assertFalse(events.exclude(actor=None).exists())
        self.assertNotIn('wrong-password',str(list(events.values())))
    def test_unknown_user_uses_standard_dummy_hash(self):
        with patch.object(User,'set_password',autospec=True) as dummy:
            self.assertIsNone(UserBackend().authenticate(None,username='unknown',password=PASSWORD));dummy.assert_called_once()
    def test_account_limit_source_rotation_xff_and_window_recovery(self):
        with patch('apps.rbac.security.ACCOUNT_LIMIT',2):
            for i in range(2):
                c=self.csrf_client();self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':'wrong'},format='json',REMOTE_ADDR='127.0.0.'+str(i+2)).status_code,401)
            c=self.csrf_client();r=c.post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json',REMOTE_ADDR='127.0.0.9',HTTP_X_FORWARDED_FOR='8.8.8.8');self.assertEqual(r.status_code,429);self.assertGreater(int(r['Retry-After']),0)
            with patch('apps.rbac.security.timezone.now',return_value=timezone.now()+timezone.timedelta(seconds=301)):
                self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json').status_code,200)
        self.user.refresh_from_db();self.assertTrue(self.user.is_active)
    def test_source_limit_username_rotation_cannot_change_xff(self):
        with patch('apps.rbac.security.SOURCE_LIMIT',2):
            for i in range(2):
                c=self.csrf_client();self.assertEqual(c.post('/api/auth/login/',{'username':'missing'+str(i),'password':'wrong'},format='json',HTTP_X_FORWARDED_FOR='1.2.3.'+str(i)).status_code,401)
            r=self.csrf_client().post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json',HTTP_X_FORWARDED_FOR='2.3.4.5');self.assertEqual(r.status_code,429)
            self.assertEqual(OperationLog.objects.filter(action='session.login_limited').count(),1)
    def test_limited_source_rotating_thousand_accounts_allocates_no_state(self):
        with patch('apps.rbac.security.SOURCE_LIMIT',2):
            for name in ['first','second']:self.assertIn('account_key',security.reserve_login(name,'127.0.0.8'))
            count=LoginWindow.objects.count()
            for i in range(1000):self.assertIn('retry_after',security.reserve_login('attack-'+str(i),'127.0.0.8'))
            self.assertEqual(LoginWindow.objects.count(),count);self.assertEqual(OperationLog.objects.filter(action='session.login_limited').count(),1)
            c=self.csrf_client();self.assertEqual(c.post('/api/auth/login/',{'username':self.root.username,'password':PASSWORD},format='json',REMOTE_ADDR='127.0.0.99').status_code,200)
        with patch('apps.rbac.security.timezone.now',return_value=timezone.now()+timezone.timedelta(seconds=301)):
            self.assertIn('account_key',security.reserve_login('after-expiry','127.0.0.8'))
            self.assertEqual(LoginWindow.objects.count(),2)
    def test_success_resets_account_not_source_and_keys_are_digests(self):
        c=self.csrf_client();c.post('/api/auth/login/',{'username':self.user.username,'password':'wrong'},format='json');self.login()
        self.assertFalse(LoginWindow.objects.filter(kind='account').exists());source=LoginWindow.objects.get(kind='source');self.assertEqual(source.attempts,2);self.assertEqual(len(source.key),64);self.assertNotIn('127.0.0.1',source.key)
    def test_capacity_and_database_failure_closed(self):
        with patch('apps.rbac.security.MAX_WINDOWS',1):
            self.assertEqual(self.csrf_client().post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json').status_code,503)
        self.assertEqual(LoginWindow.objects.count(),0)
        from django.db import OperationalError
        with patch.object(LoginWindow.objects,'count',side_effect=OperationalError('sensitive marker')):
            r=self.csrf_client().post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json');self.assertEqual(r.status_code,503);self.assertNotIn('sensitive',str(r.data))
    def test_csrf_origin_fail_before_attempt_side_effect(self):
        c=APIClient(enforce_csrf_checks=True);self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json').status_code,403)
        c=self.csrf_client();self.assertEqual(c.post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json',HTTP_ORIGIN='https://evil.invalid').status_code,403);self.assertEqual(LoginWindow.objects.count(),0)
    def test_login_audit_failure_establishes_no_usable_session(self):
        c=self.csrf_client()
        with patch('apps.audit.service.record',side_effect=RuntimeError('secret-marker')):
            r=c.post('/api/auth/login/',{'username':self.user.username,'password':PASSWORD},format='json');self.assertEqual(r.status_code,503);self.assertNotIn('secret-marker',str(r.data))
        self.assertEqual(c.get('/api/auth/user-info/').status_code,403);self.assertEqual(ManagedSession.objects.count(),0)
    def test_list_safe_independent_handles_and_other_revoke(self):
        first=self.login();second=self.login();raw=first.cookies['sessionid'].value;rows=first.get('/api/auth/sessions/').data['data'];self.assertEqual(len(rows),2)
        for row in rows:
            self.assertEqual(set(row),{'id','created_at','expires_at','current'});uuid.UUID(row['id']);self.assertNotEqual(row['id'],raw)
        self.assertNotIn(raw,str(rows));self.assertEqual(sum(x['current'] for x in rows),1)
        self.assertEqual(first.post('/api/auth/revoke-other-sessions/',{},format='json').data['data']['revoked'],1);self.assertEqual(first.get('/api/auth/user-info/').status_code,200);self.assertEqual(second.get('/api/auth/user-info/').status_code,403)
    def test_handle_single_cross_user_idempotent_and_csrf(self):
        first=self.login();second=self.login();other=self.login(self.root);rows=first.get('/api/auth/sessions/').data['data'];handle=next(x['id'] for x in rows if not x['current'])
        self.assertEqual(other.post('/api/auth/revoke-session/',{'id':handle},format='json').data['data']['revoked'],0)
        self.assertEqual(first.post('/api/auth/revoke-session/',{'id':handle},format='json').data['data']['revoked'],1);self.assertEqual(first.post('/api/auth/revoke-session/',{'id':handle},format='json').data['data']['revoked'],0);self.assertEqual(second.get('/api/auth/user-info/').status_code,403)
        first.credentials();self.assertEqual(first.post('/api/auth/revoke-other-sessions/',{},format='json').status_code,403)
    def test_admin_all_revoke_and_self_current_rule(self):
        user1=self.login();user2=self.login();admin=self.login(self.root)
        r=admin.post('/api/auth/revoke-user-sessions/',{'user_id':self.user.pk},format='json');self.assertEqual(r.status_code,200);self.assertEqual(r.data['data']['revoked'],2)
        self.assertEqual(user1.get('/api/auth/user-info/').status_code,403);self.assertEqual(user2.get('/api/auth/user-info/').status_code,403);self.assertEqual(admin.get('/api/auth/user-info/').status_code,200)
        r=admin.post('/api/auth/revoke-user-sessions/',{'user_id':self.root.pk},format='json');self.assertTrue(r.data['data']['current_revoked']);self.assertEqual(admin.get('/api/auth/user-info/').status_code,403)
    def test_service_missing_nonroot_boss_and_custom_cannot_revoke_any_target(self):
        boss_role=Role.objects.create(name='Security boss',code='boss');boss=User.objects.create_user('security-boss','b@security.invalid',PASSWORD);UserRole.objects.create(user=boss,role=boss_role)
        role=Role.objects.create(name='Security writer',code='security_writer');UserRole.objects.create(user=self.user,role=role);RolePermission.objects.create(role=role,permission_code='users.write')
        for actor in [None,self.user,boss]:
            for target in [self.root,self.user]:
                with self.assertRaises(BusinessError):security.revoke_sessions(actor,target_id=target.pk)
        c=self.login(boss);self.assertEqual(c.post('/api/auth/revoke-user-sessions/',{'user_id':self.root.pk},format='json').status_code,403)
    def test_current_roles_rechecked_for_existing_sessions(self):
        role=Role.objects.create(name='Security root',code='root');self.root.is_superuser=False;self.root.save();UserRole.objects.create(user=self.root,role=role);admin=self.login(self.root)
        UserRole.objects.filter(user=self.root).delete();self.assertEqual(admin.post('/api/auth/revoke-user-sessions/',{'user_id':self.user.pk},format='json').status_code,403)
        role2=Role.objects.create(name='Security audit',code='security_audit');UserRole.objects.create(user=self.user,role=role2);RolePermission.objects.create(role=role2,permission_code='audit.read');c=self.login();self.assertEqual(c.get('/api/audit/logs/').status_code,200);role2.soft_delete();self.assertEqual(c.get('/api/audit/logs/').status_code,403)
    def test_preupgrade_session_registered_lazily_and_revoked(self):
        c=APIClient(enforce_csrf_checks=True);c.force_login(self.user,backend='apps.rbac.backends.UserBackend');c.get('/api/auth/csrf/');c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value);self.assertEqual(ManagedSession.objects.count(),0);self.assertEqual(len(c.get('/api/auth/sessions/').data['data']),1)
        admin=self.login(self.root);self.assertEqual(admin.post('/api/auth/revoke-user-sessions/',{'user_id':self.user.pk},format='json').data['data']['revoked'],1);self.assertEqual(c.get('/api/auth/user-info/').status_code,403)
    def test_legacy_never_listed_session_revoked_and_fallback_recognized(self):
        from django.conf import settings
        from django.test import override_settings
        old=APIClient();old.force_login(self.user,backend='apps.rbac.backends.UserBackend');self.assertEqual(ManagedSession.objects.count(),0)
        admin=self.login(self.root);self.assertEqual(admin.post('/api/auth/revoke-user-sessions/',{'user_id':self.user.pk},format='json').data['data']['revoked'],1);self.assertEqual(old.get('/api/auth/user-info/').status_code,403)
        secret=settings.SECRET_KEY
        legacy=APIClient();legacy.force_login(self.user,backend='apps.rbac.backends.UserBackend')
        with override_settings(SECRET_KEY='new-process-secret-for-fallback-tests',SECRET_KEY_FALLBACKS=[secret]):
            result=security.revoke_sessions(self.root,target_id=self.user.pk);self.assertEqual(result['revoked'],1);self.assertEqual(legacy.get('/api/auth/user-info/').status_code,403)
    def test_revoke_audit_failure_rolls_back_sessions(self):
        first=self.login();second=self.login()
        with patch('apps.audit.service.record',side_effect=RuntimeError('synthetic-failure')):
            with self.assertRaises(RuntimeError):security.revoke_sessions(self.user,first.cookies['sessionid'].value,others=True)
        self.assertEqual(second.get('/api/auth/user-info/').status_code,200)
    def test_unknown_fields_and_invalid_handle_rejected(self):
        c=self.login()
        for path,data in [('revoke-other-sessions',{'user_id':self.root.pk}),('revoke-session',{'id':'bad'}),('revoke-user-sessions',{'user_id':-1})]:
            self.assertEqual(c.post('/api/auth/'+path+'/',data,format='json').status_code,400)
        self.assertEqual(c.get('/api/auth/sessions/?user_id=1').status_code,400)

from django.test import TransactionTestCase
from django.db import connections
import threading

class LoginConcurrencyTests(TransactionTestCase):
    def test_two_connections_do_not_oversubscribe(self):
        barrier=threading.Barrier(2);results=[];lock=threading.Lock()
        def worker():
            try:
                barrier.wait(timeout=10);value=security.reserve_login('race-account','127.0.0.42');result='reserved' if 'account_key' in value else 'limited' if 'retry_after' in value else 'closed'
            except BusinessError as error:result=error.code
            except Exception as error:result=type(error).__name__
            finally:connections.close_all()
            with lock:results.append(result)
        with patch('apps.rbac.security.ACCOUNT_LIMIT',1):
            threads=[threading.Thread(target=worker) for _ in range(2)]
            for t in threads:t.start()
            for t in threads:t.join(timeout=20);self.assertFalse(t.is_alive())
        self.assertEqual(len(results),2);self.assertEqual(results.count('reserved'),1,results);self.assertTrue(set(results)<={'reserved','limited','SECURITY_UNAVAILABLE'},results)
        self.assertEqual(LoginWindow.objects.get(kind='account').attempts,1);self.assertEqual(LoginWindow.objects.get(kind='source').attempts,1)
        print('login two-connection outcomes:',sorted(results),flush=True)

