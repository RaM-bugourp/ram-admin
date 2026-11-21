from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for rel,functions in [('backend/apps/rbac/services/user_service.py',['create_user','update_user','delete_user','reset_password','create_from_approval']),('backend/apps/rbac/services/role_service.py',['create_role','update_role','delete_role']),('backend/apps/ai/services/ai_approval.py',['review'])]:
 p=ROOT/rel;s=p.read_text(encoding='utf-8');lines=s.splitlines();result=[]
 for line in lines:
  result.append(line)
  if any(line.lstrip().startswith('def '+name+'(') for name in functions):
   # Single-line definitions only in current scoped implementation.
   assert line.rstrip().endswith(':')
   indent=' '*(len(line)-len(line.lstrip())+4)
   if 'create_from_approval' in line:
    # Preserve method docstring as first statement; insert after it below.
    pass
   else:result.extend([indent+'from apps.rbac.services.locking import reserve_lifecycle_write',indent+'reserve_lifecycle_write()'])
 text='\n'.join(result)+'\n'
 if 'create_from_approval' in functions:
  old='        """Private approval capability: persisted approved row bound to current root reviewer."""'
  assert old in text;text=text.replace(old,old+'\n        from apps.rbac.services.locking import reserve_lifecycle_write\n        reserve_lifecycle_write()')
 p.write_text(text,encoding='utf-8')
print('SQLite lifecycle write reservation connected')
