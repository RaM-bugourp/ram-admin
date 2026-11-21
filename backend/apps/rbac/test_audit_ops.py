import csv,io
from unittest.mock import patch
from django.test import TestCase
from rest_framework.test import APIClient
from apps.rbac.models import User,Role,UserRole,RolePermission
from apps.audit.models import OperationLog
from apps.audit.query import csv_cell

class AuditOpsTests(TestCase):
    def setUp(self):
        self.root=User.objects.create_user('csv-root','private-email@invalid.test','Synthetic-Only-845!',is_superuser=True)
        self.user=User.objects.create_user('csv-user','private-user@invalid.test',None)
        self.c=APIClient();self.c.force_authenticate(self.root)
    def test_list_and_csv_same_filters_and_safe_whitelist(self):
        OperationLog.objects.create(actor=self.root,action='user.csv',resource='user',object_id='1')
        OperationLog.objects.create(actor=self.user,action='user.csv',resource='user',object_id='2')
        query=f'action=user.csv&actor_id={self.root.pk}&start=2026-01-01T00:00:00%2B08:00&end=2030-01-01T00:00:00%2B08:00'
        listed=self.c.get('/api/audit/logs/?'+query);exported=self.c.get('/api/audit/export/?'+query,HTTP_ACCEPT='text/csv')
        self.assertEqual(listed.status_code,200);self.assertEqual(exported.status_code,200)
        self.assertTrue(exported.content.startswith(b'\xef\xbb\xbf'));rows=list(csv.DictReader(io.StringIO(exported.content.decode('utf-8-sig'))));self.assertEqual([str(x['id']) for x in listed.data['data']],[x['id'] for x in rows]);self.assertEqual(len(rows),1)
        self.assertNotIn('private-email',exported.content.decode());self.assertEqual(exported['Cache-Control'],'no-store');self.assertEqual(set(rows[0]),{'id','actor_id','actor_name','action','resource','object_id','outcome','created_at'});self.assertEqual(OperationLog.objects.filter(action='audit.export').count(),1)
    def test_invalid_calendar_reverse_unknown_duplicates_both_endpoints(self):
        for q in ['start=2026-02-30T00:00:00%2B08:00','start=2026-01-01','start=2027-01-01T00:00:00Z&end=2026-01-01T00:00:00Z','secret=1','action=a&action=b','actor_id=-1']:
            for endpoint in ['logs','export']:self.assertEqual(self.c.get('/api/audit/'+endpoint+'/?'+q).status_code,400,q)
    def test_formula_dangerous_whitespace_controls_quotes_unicode(self):
        samples=['=1+1','+SUM(A1)','-2+3','@cmd',' \t=1','\r\n+cmd','\t@cmd','中文,"引用"\r\n=1']
        for index,value in enumerate(samples):OperationLog.objects.create(actor=self.root,action='csv.formula',resource='audit',object_id=value)
        r=self.c.get('/api/audit/export/?action=csv.formula');self.assertEqual(r.status_code,200)
        rows=list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig'))));self.assertEqual(len(rows),len(samples))
        for row in rows:
            value=row['object_id'];self.assertNotIn('\r',value);self.assertNotIn('\n',value);self.assertNotIn('\t',value);self.assertFalse(value.lstrip().startswith(('=','+','-','@')))
        for value in samples[:7]:self.assertTrue(csv_cell(value).startswith("'"))
    def test_permission_explicit_reader_nonroot_and_revocation(self):
        c=APIClient();c.force_authenticate(self.user);self.assertEqual(c.get('/api/audit/export/').status_code,403)
        role=Role.objects.create(name='CSV reader',code='csv_reader');UserRole.objects.create(user=self.user,role=role);RolePermission.objects.create(role=role,permission_code='audit.read');self.assertEqual(c.get('/api/audit/export/').status_code,200);role.soft_delete();self.assertEqual(c.get('/api/audit/export/').status_code,403)
    def test_limit_rejects_no_silent_truncation(self):
        for i in range(3):OperationLog.objects.create(actor=self.root,action='csv.limit',resource='audit')
        with patch('apps.audit.query.EXPORT_LIMIT',2):
            r=self.c.get('/api/audit/export/?action=csv.limit');self.assertEqual(r.status_code,400);self.assertEqual(OperationLog.objects.filter(action='audit.export').count(),0)
    def test_export_audit_unavailable_never_returns_csv(self):
        with patch('apps.audit.service.record',side_effect=RuntimeError('secret-marker')):
            with self.assertRaises(RuntimeError):self.c.get('/api/audit/export/')
        self.assertEqual(OperationLog.objects.filter(action='audit.export').count(),0)
