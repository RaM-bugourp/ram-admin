"""CORE-002 synthetic ORM/API regression; real browser is separate."""
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from apps.common.exceptions import BusinessError
from apps.rbac.models import User, Role, UserRole
from apps.rbac.permissions import has_role
from apps.rbac.services.user_service import UserService
from apps.ai.permissions import AgentTokenService
from apps.ai.models import AIApproval, AIApprovalLog, AICallLog

class CoreSecurityTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_user('core-root','root@core.invalid','Synthetic-Only-845!',is_superuser=True)
        self.user = User.objects.create_user('core-user','user@core.invalid','Synthetic-Only-845!')
        self.role = Role.objects.create(name='root',code='root')
        self.link = UserRole.objects.create(user=self.user,role=self.role)

    def test_none_actor_cannot_create(self):
        with self.assertRaises(BusinessError):
            UserService().create_user({'username':'untrusted','email':'u@core.invalid','password':'Synthetic-Only-845!'})
        self.assertFalse(User.objects.filter(username='untrusted').exists())

    def test_none_actor_cannot_update_delete_reset(self):
        service=UserService()
        for fn,args in [(service.update_user,(self.user.pk,{'email':'bad@core.invalid'})),(service.delete_user,(self.user.pk,)),(service.reset_password,(self.user.pk,'Changed-Only-845!'))]:
            with self.subTest(fn=fn.__name__),self.assertRaises(BusinessError): fn(*args)

    def test_deleted_role_is_not_effective(self):
        self.role.soft_delete()
        self.assertFalse(has_role(self.user,'root'))

    def submit(self):
        token=AgentTokenService.issue(root_user_id=self.root.pk,agent_id='core-agent')
        return APIClient().post('/api/ai/approval/submit/',{'agent_id':'forged','operation':'create_user','params':{'username':'new-core','email':'new@core.invalid','password':'Private-Only-987!'},'reason':'synthetic'},format='json',HTTP_X_AGENT_TOKEN=token)

    def test_submission_attributed_to_actual_issuer(self):
        response=self.submit(); self.assertEqual(response.status_code,201)
        approval=AIApproval.objects.get()
        self.assertEqual(getattr(approval,'submitted_by_id',None),self.root.pk)
        self.assertEqual(AIApprovalLog.objects.get(action='submit').root_user_id,self.root.pk)
        self.assertEqual(AICallLog.objects.get().root_user_id,self.root.pk)

    def test_submission_secret_not_in_audit_or_response_or_raw_storage(self):
        response=self.submit(); self.assertEqual(response.status_code,201)
        self.assertNotIn('Private-Only-987!',str(response.data))
        self.assertNotIn('Private-Only-987!',str(list(AICallLog.objects.values())))
        self.assertNotIn('Private-Only-987!',str(AIApproval.objects.get().params))

    def test_submission_and_audit_are_one_transaction(self):
        with patch('apps.ai.services.ai_audit.AIAuditService.log_agent_submission',side_effect=RuntimeError('synthetic audit failure')):
            with self.assertRaises(RuntimeError): self.submit()
        self.assertEqual(AIApproval.objects.count(),0)
        self.assertEqual(AIApprovalLog.objects.count(),0)
