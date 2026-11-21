"""Real ORM/SQLite and DRF test-client coverage; not browser/HTTP E2E."""
import hashlib
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.db import OperationalError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.ai.models import AgentCredential, AIApproval, AIApprovalLog, AICallLog
from apps.ai.permissions import AgentTokenService, AgentTokenUnavailable, _has_root_role
from apps.rbac.models import User, Role, UserRole


class TokenTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role = Role.objects.create(code='root', name='root')
        cls.root = User.objects.create_user(username='root-synthetic', email='root@example.invalid', password='Synthetic-Only-845!')
        cls.link = UserRole.objects.create(user=cls.root, role=cls.role)
        cls.other = User.objects.create_user(username='other-root', email='other@example.invalid', password=None, is_superuser=True)
        cls.user = User.objects.create_user(username='ordinary', email='ordinary@example.invalid', password=None)

    def issue(self, agent='agent.with.dots', issuer=None):
        return AgentTokenService.issue(root_user_id=(issuer or self.root).pk, agent_id=agent)

    def credential(self, token):
        return AgentCredential.objects.get(token_digest=hashlib.sha256(token.encode()).hexdigest())

    def submit(self, token=None, client=None):
        headers = {'HTTP_X_AGENT_TOKEN': token} if token is not None else {}
        return (client or APIClient()).post('/api/ai/approval/submit/', {'agent_id': 'forged-body-agent', 'operation': 'create_user', 'params': {'username': 'must-not-exist', 'email': 'never@example.invalid', 'password': 'Not-Executed-845!'}, 'reason': 'synthetic'}, format='json', **headers)

    def assert_denied_without_effect(self, token, client=None):
        before = (AIApproval.objects.count(), AIApprovalLog.objects.count(), AICallLog.objects.count(), User.objects.count())
        self.assertEqual(self.submit(token, client).status_code, 403)
        self.assertEqual(before, (AIApproval.objects.count(), AIApprovalLog.objects.count(), AICallLog.objects.count(), User.objects.count()))

    def test_valid_agent_submits_pending_with_bound_identity(self):
        token = self.issue()
        response = self.submit(token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['agent_id'], 'agent.with.dots')
        self.assertEqual(response.data['data']['status'], 'pending')
        self.assertFalse(User.objects.filter(username='must-not-exist').exists())

    def test_correctly_signed_unregistered_and_digest_mismatch_denied(self):
        import hmac
        from django.conf import settings
        body = 'v2.' + uuid.uuid4().hex
        signed = body + '.' + hmac.new(settings.AI_AGENT_TOKEN_SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
        self.assertIsNone(AgentTokenService.verify(signed))
        self.assert_denied_without_effect(signed)
        token = self.issue()
        AgentCredential.objects.filter(pk=self.credential(token).pk).update(token_digest='0'*64)
        self.assertIsNone(AgentTokenService.verify(token))
        self.assert_denied_without_effect(token)

    def test_logged_in_root_loses_issuer_privileges_before_issue_and_revoke(self):
        for mutation in ['disabled', 'soft-deleted', 'unlinked', 'role-deleted']:
            with self.subTest(mutation=mutation):
                c = self.login_csrf_client()
                c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)
                token = self.issue()
                row = self.credential(token)
                if mutation == 'disabled': User.objects.filter(pk=self.root.pk).update(is_active=False)
                elif mutation == 'soft-deleted': User.objects.filter(pk=self.root.pk).update(is_deleted=True)
                elif mutation == 'unlinked': UserRole.objects.filter(pk=self.link.pk).update(is_deleted=True)
                else: Role.objects.filter(pk=self.role.pk).update(is_deleted=True)
                before = AgentCredential.objects.count()
                self.assertEqual(c.post('/api/ai/agent-token/issue/', {'agent_id':'new'}, format='json').status_code, 403)
                self.assertEqual(c.post('/api/ai/agent-token/revoke/', {'token_id':str(row.pk)}, format='json').status_code, 403)
                self.assertEqual(AgentCredential.objects.count(), before)
                row.refresh_from_db(); self.assertIsNone(row.revoked_at)
                User.objects.with_deleted().filter(pk=self.root.pk).update(is_active=True,is_deleted=False)
                UserRole.objects.with_deleted().filter(pk=self.link.pk).update(is_deleted=False)
                Role.objects.with_deleted().filter(pk=self.role.pk).update(is_deleted=False)

    def test_registry_never_stores_raw_token(self):
        token = self.issue()
        row = self.credential(token)
        self.assertEqual(row.token_digest, hashlib.sha256(token.encode()).hexdigest())
        self.assertNotIn(token, str(AgentCredential.objects.values().get(pk=row.pk)))
        self.assertNotIn('token', [f.name for f in AgentCredential._meta.fields])

    def test_same_moment_issuance_is_distinct_and_revocation_permanent(self):
        with patch('apps.ai.permissions.timezone.now', return_value=timezone.now()):
            first, second = self.issue(), self.issue()
        self.assertNotEqual(first, second)
        row = self.credential(first)
        AgentTokenService.revoke(token_id=row.pk, actor=self.root)
        AgentTokenService.revoke(token_id=row.pk, actor=self.root)
        self.assert_denied_without_effect(first)
        self.assertIsNotNone(AgentTokenService.verify(second))
        self.assertIsNotNone(AgentTokenService.verify(self.issue()))
        self.assertIsNone(AgentTokenService.verify(first))

    def test_revoke_unknown_is_idempotent_and_other_root_can_revoke(self):
        token = self.issue()
        AgentTokenService.revoke(token_id=uuid.uuid4(), actor=self.other)
        AgentTokenService.revoke(token_id=self.credential(token).pk, actor=self.other)
        self.assertIsNone(AgentTokenService.verify(token))

    def test_cross_agent_and_issuer_isolation(self):
        first, second, third = self.issue('a'), self.issue('b'), self.issue('a', self.other)
        AgentTokenService.revoke(token_id=self.credential(first).pk, actor=self.root)
        self.assertIsNone(AgentTokenService.verify(first))
        self.assertEqual(AgentTokenService.verify(second)['agent_id'], 'b')
        self.assertEqual(AgentTokenService.verify(third)['root_user_id'], self.other.pk)

    def test_disabled_issuer_denied_then_restored_unrevoked_can_resume(self):
        token = self.issue()
        User.objects.filter(pk=self.root.pk).update(is_active=False)
        self.assert_denied_without_effect(token)
        self.assertFalse(_has_root_role(self.root))
        User.objects.filter(pk=self.root.pk).update(is_active=True)
        self.assertIsNotNone(AgentTokenService.verify(token))

    def test_soft_deleted_issuer_denied(self):
        token = self.issue()
        User.objects.filter(pk=self.root.pk).update(is_deleted=True)
        self.assert_denied_without_effect(token)

    def test_hard_deleted_issuer_denied(self):
        token = self.issue()
        self.root.delete()
        self.assert_denied_without_effect(token)
        self.assertEqual(AgentCredential.objects.count(), 0)

    def test_removed_root_association_denied(self):
        token = self.issue()
        self.link.delete()
        self.assert_denied_without_effect(token)

    def test_soft_deleted_root_association_denied(self):
        token = self.issue()
        UserRole.objects.filter(pk=self.link.pk).update(is_deleted=True)
        self.assert_denied_without_effect(token)

    def test_soft_deleted_root_role_denied(self):
        token = self.issue()
        Role.objects.filter(pk=self.role.pk).update(is_deleted=True)
        self.assert_denied_without_effect(token)

    def test_superuser_without_role_valid_but_disabled_and_demoted_denied(self):
        token = self.issue(issuer=self.other)
        self.assertIsNotNone(AgentTokenService.verify(token))
        User.objects.filter(pk=self.other.pk).update(is_active=False)
        self.assert_denied_without_effect(token)
        User.objects.filter(pk=self.other.pk).update(is_active=True, is_superuser=False)
        self.assert_denied_without_effect(token)

    def test_expiry_equal_now_and_past_are_denied(self):
        token = self.issue()
        now = timezone.now()
        AgentCredential.objects.filter(pk=self.credential(token).pk).update(expires_at=now)
        with patch('apps.ai.permissions.timezone.now', return_value=now):
            self.assertIsNone(AgentTokenService.verify(token))
        AgentCredential.objects.update(expires_at=now-timedelta(seconds=1))
        self.assert_denied_without_effect(token)

    def test_malformed_legacy_unknown_tampered_unicode_denied(self):
        token = self.issue()
        for bad in [None, '', '1.2.legacy.' + 'a'*64, 'v2.'+'a'*32+'.'+'a'*64, token[:-1]+('a' if token[-1]!='a' else 'b'), token[:-1]+'中', 'v2.💥.bad', 'x'*1000]:
            with self.subTest(kind=type(bad).__name__, size=len(bad or '')):
                self.assertIsNone(AgentTokenService.verify(bad))
        self.assert_denied_without_effect('1.2.legacy.' + 'a'*64)
        self.assert_denied_without_effect(None)

    def test_secret_missing_short_wrong_type_fail_closed(self):
        token = self.issue()
        for value in ['', 'short', None, 123]:
            with self.subTest(kind=type(value).__name__), override_settings(AI_AGENT_TOKEN_SECRET=value):
                self.assertIsNone(AgentTokenService.verify(token))
                with self.assertRaises(AgentTokenUnavailable):
                    self.issue()

    def test_secret_rotation_invalidates_old_tokens(self):
        token = self.issue()
        with override_settings(AI_AGENT_TOKEN_SECRET='different-test-only-'+'x'*48):
            self.assertIsNone(AgentTokenService.verify(token))
            self.assertIsNotNone(AgentTokenService.verify(self.issue()))

    def test_service_rejects_invalid_issuer_agent_ttl(self):
        with self.assertRaises(PermissionDenied):
            self.issue(issuer=self.user)
        for agent, ttl in [('',24), ('x'*101,24), ('a',0), ('a',721), ('a',True)]:
            with self.assertRaises(ValidationError):
                AgentTokenService.issue(root_user_id=self.root.pk, agent_id=agent, ttl_hours=ttl)
        with self.assertRaises(PermissionDenied):
            AgentTokenService.revoke(token_id=uuid.uuid4(), actor=self.user)

    def test_database_error_never_falls_back_to_signature_only(self):
        token = self.issue()
        with patch('apps.ai.models.AgentCredential.objects.select_related', side_effect=OperationalError('synthetic db unavailable')):
            self.assert_denied_without_effect(token)
        with patch('apps.ai.models.AgentCredential.objects.create', side_effect=OperationalError('synthetic db unavailable')):
            with self.assertRaises(OperationalError): self.issue()
        with patch('apps.ai.models.AgentCredential.objects.filter', side_effect=OperationalError('synthetic db unavailable')):
            with self.assertRaises(OperationalError):
                AgentTokenService.revoke(token_id=self.credential(token).pk, actor=self.root)

    def test_agent_does_not_gain_other_root_or_rbac_endpoints(self):
        token = self.issue()
        c = APIClient()
        c.credentials(HTTP_X_AGENT_TOKEN=token)
        for method, path, body in [('post','/api/ai/agent-token/issue/',{'agent_id':'x'}),('post','/api/ai/agent-token/revoke/',{'token_id':str(uuid.uuid4())}),('get','/api/ai/approval/',{}),('post','/api/ai/approval/999/review/',{'action':'approve'}),('post','/api/ai/chat/chat/',{'message':'must not call provider'}),('get','/api/rbac/users/',{})]:
            with self.subTest(path=path):
                self.assertEqual(getattr(c,method)(path,body,format='json').status_code,403)

    def login_csrf_client(self):
        c = APIClient(enforce_csrf_checks=True)
        c.get('/api/auth/csrf/')
        response = c.post('/api/auth/login/', {'username':self.root.username,'password':'Synthetic-Only-845!'},format='json',HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)
        self.assertEqual(response.status_code,200)
        return c

    def test_real_session_issue_revoke_csrf_and_consumer_response(self):
        c = self.login_csrf_client()
        self.assertEqual(c.post('/api/ai/agent-token/issue/',{'agent_id':'x'},format='json').status_code,403)
        c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)
        response = c.post('/api/ai/agent-token/issue/',{'agent_id':'agent.with.dots','ttl_hours':1},format='json')
        self.assertEqual(response.status_code,200)
        data = response.data['data']
        self.assertTrue({'token','agent_id','expires_in_hours','note','token_id'} <= data.keys())
        self.assertEqual(data['expires_in_hours'],1)
        self.assertEqual(AgentTokenService.verify(data['token'])['agent_id'],'agent.with.dots')
        logs = str(list(AICallLog.objects.values('prompt','response')))
        self.assertNotIn(data['token'],logs)
        self.assertNotIn(data['token'][:12],logs)
        c.credentials()
        self.assertEqual(c.post('/api/ai/agent-token/revoke/',{'token_id':data['token_id']},format='json').status_code,403)
        c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)
        for _ in range(2):
            self.assertEqual(c.post('/api/ai/agent-token/revoke/',{'token_id':data['token_id']},format='json').status_code,200)
        self.assert_denied_without_effect(data['token'])
        self.assertEqual(c.post('/api/ai/agent-token/revoke/',{'token_id':'bad'},format='json').status_code,400)

    def test_valid_root_session_independent_of_invalid_agent_header(self):
        c = self.login_csrf_client()
        c.credentials(HTTP_X_CSRFTOKEN=c.cookies['csrftoken'].value)
        self.assertEqual(self.submit('invalid', c).status_code,201)

    def test_ordinary_session_bad_token_does_not_fall_back(self):
        c = APIClient()
        c.force_authenticate(self.user)
        self.assert_denied_without_effect('invalid', c)

    def test_issue_api_input_boundaries_and_missing_configuration(self):
        c = APIClient()
        c.force_authenticate(self.root)
        for ttl in [0,721]:
            self.assertEqual(c.post('/api/ai/agent-token/issue/',{'agent_id':'x','ttl_hours':ttl},format='json').status_code,400)
        with override_settings(AI_AGENT_TOKEN_SECRET=''):
            self.assertEqual(c.post('/api/ai/agent-token/issue/',{'agent_id':'x'},format='json').status_code,503)
