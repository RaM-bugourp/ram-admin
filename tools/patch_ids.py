from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['backend/apps/rbac/views/user_views.py','backend/apps/rbac/views/role_views.py','backend/apps/ai/views/approval_views.py']:
 p=ROOT/name;s=p.read_text(encoding='utf-8');assert 'int(pk)' in s
 s='from apps.common.inputs import positive_int\n'+s
 p.write_text(s.replace('int(pk)',"positive_int(pk, 'id')"),encoding='utf-8')
print('invalid resource ID input guards connected')
