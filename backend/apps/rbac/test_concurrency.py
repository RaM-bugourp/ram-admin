"""Two real SQLite connections. No throughput/capacity or other-engine claim."""
import threading
from django.test import TransactionTestCase,override_settings
from django.db import connections
from apps.rbac.models import User,Role,UserRole
from apps.rbac.services.user_service import UserService
from apps.ai.services.ai_approval import AIApprovalService
from apps.ai.services.approval_params import prepare
from apps.ai.models import AIApproval

class SQLiteLifecycleConcurrencyTests(TransactionTestCase):
 def race(self,operations):
  barrier=threading.Barrier(len(operations));results=[];lock=threading.Lock()
  def worker(operation):
   try:
    barrier.wait(timeout=10);operation();result='success'
   except Exception as error:result=getattr(error,'code',None) or type(error).__name__
   finally:connections.close_all()
   with lock:results.append(result)
  threads=[threading.Thread(target=worker,args=(op,)) for op in operations]
  for thread in threads:thread.start()
  for thread in threads:thread.join(timeout=25);self.assertFalse(thread.is_alive())
  self.assertEqual(len(results),len(operations))
  self.assertEqual(results.count('success'),1,results)
  self.assertTrue(set(results)<={'success','PERMISSION_DENIED','LAST_ROOT_PROTECTED','UNIQUE_ROLE_CONFLICT','APPROVAL_ALREADY_PROCESSED','CONCURRENT_CONFLICT'},results)
  print('two-connection outcomes:',sorted(results),flush=True)
  return results
 def test_parallel_last_root_revocation_never_removes_all_roots(self):
  first=User.objects.create_user('race-root-a','a@race.invalid',None,is_superuser=True);second=User.objects.create_user('race-root-b','b@race.invalid',None,is_superuser=True)
  results=self.race([lambda:UserService().update_user(first.pk,{'is_active':False},actor=second),lambda:UserService().update_user(second.pk,{'is_active':False},actor=first)])
  self.assertEqual(User.objects.filter(is_active=True,is_superuser=True).count(),1);self.assertEqual(results.count('success'),1)
 def test_parallel_unique_role_assignment_has_one_holder(self):
  root=User.objects.create_user('race-root','root@race.invalid',None,is_superuser=True);first=User.objects.create_user('race-a','a@race.invalid',None);second=User.objects.create_user('race-b','b@race.invalid',None);role=Role.objects.create(name='race-unique',code='race_unique',is_unique=True)
  results=self.race([lambda:UserService().update_user(first.pk,{'role_ids':[role.pk]},actor=root),lambda:UserService().update_user(second.pk,{'role_ids':[role.pk]},actor=root)])
  self.assertEqual(UserRole.objects.filter(role=role).count(),1);self.assertEqual(results.count('success'),1)
 @override_settings(AI_APPROVAL_AUTO_EXECUTE=True)
 def test_parallel_approval_review_executes_once(self):
  root=User.objects.create_user('race-root','root@race.invalid',None,is_superuser=True)
  approval=AIApprovalService().submit_operation(agent_id='race-agent',operation='create_user',params={'username':'race-created','email':'created@race.invalid','password':'Synthetic-Only-987!'},reason='',root_user=root)
  results=self.race([lambda:AIApprovalService().review(approval_id=approval.pk,root_user=root,action='approve'),lambda:AIApprovalService().review(approval_id=approval.pk,root_user=root,action='approve')])
  self.assertEqual(User.objects.filter(username='race-created').count(),1);approval.refresh_from_db();self.assertEqual(approval.status,'executed');self.assertEqual(results.count('success'),1)
