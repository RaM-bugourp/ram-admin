"""Local operator only; no HTTP caller, arbitrary path input, or live replacement.

Backups contain password hashes and active sessions. Keep secrets/config separately.
Restored sessions/tokens remain valid under the SAME secret until expiry/revocation;
never expose a restored clone to a public listener. IDs are not authorization.
"""
from contextlib import closing
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import stat
import subprocess
import time
import uuid
from pathlib import Path
from django.conf import settings
from django.db import connection

ROOT = Path(__file__).resolve().parents[3]
PRIVATE = ROOT / '.private-ops'
ID = re.compile(r'[0-9a-f]{32}')

class OpsError(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)

def _unlinked(path):
    path=Path(path).absolute()
    for item in [path,*path.parents]:
        if item.exists() or item.is_symlink():
            attrs=item.lstat()
            if item.is_symlink() or getattr(attrs,'st_file_attributes',0)&0x400:
                raise OpsError('LINK_PATH_REJECTED')
    return path

def _private(path, directory=False):
    _unlinked(path)
    if os.name=='nt':
        result=subprocess.run(['whoami','/user','/fo','csv','/nh'],capture_output=True,text=True,check=True)
        sid=list(csv.reader(io.StringIO(result.stdout.strip())))[0][-1]
        if not re.fullmatch(r'S-1-[0-9-]+',sid):raise OpsError('PRIVATE_ACL_UNAVAILABLE')
        # Replace all DACL entries, not just inheritance (explicit Everyone must not survive).
        import ctypes
        from ctypes import wintypes
        flags='OICI' if directory else ''
        sddl='D:P'+''.join(f'(A;{flags};FA;;;{s})' for s in [sid,'SY','BA'])
        adv=ctypes.WinDLL('advapi32',use_last_error=True)
        convert=adv.ConvertStringSecurityDescriptorToSecurityDescriptorW
        convert.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.POINTER(ctypes.c_void_p),ctypes.POINTER(wintypes.DWORD)]
        convert.restype=wintypes.BOOL
        apply=adv.SetFileSecurityW;apply.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,ctypes.c_void_p];apply.restype=wintypes.BOOL
        descriptor=ctypes.c_void_p()
        if not convert(sddl,1,ctypes.byref(descriptor),None):raise OpsError('PRIVATE_ACL_UNAVAILABLE')
        try:
            # DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION only.
            if not apply(str(path),0x80000004,descriptor):raise OpsError('PRIVATE_ACL_UNAVAILABLE')
        finally:ctypes.windll.kernel32.LocalFree(descriptor)
    else:path.chmod(0o700 if directory else 0o600)

def _base():
    if PRIVATE!=ROOT/'.private-ops':raise OpsError('PRIVATE_ROOT_INVALID')
    _unlinked(PRIVATE)
    if not PRIVATE.exists():PRIVATE.mkdir(mode=0o700)
    _private(PRIVATE,True)
    for name in ('backups','restores'):
        p=PRIVATE/name;_unlinked(p)
        if not p.exists():p.mkdir(mode=0o700)
        _private(p,True)
    return PRIVATE

def _id(value):
    if not isinstance(value,str) or not ID.fullmatch(value):raise OpsError('INVALID_BACKUP_ID')
    return value

def _source():
    if connection.vendor!='sqlite':raise OpsError('SQLITE_ONLY')
    name=connection.settings_dict['NAME']
    if str(name)==':memory:' or not Path(name).is_absolute():raise OpsError('ABSOLUTE_FILE_DATABASE_REQUIRED')
    source=_unlinked(Path(name))
    if not source.is_file():raise OpsError('SOURCE_UNAVAILABLE')
    return source

def _connect_ro(path):
    return sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=10)

from functools import lru_cache

@lru_cache(maxsize=1)
def _expected_schema():
    # A separate process whose DEFAULT is memory is essential: historical RunPython
    # migrations use unqualified managers. A secondary alias could touch caller default!
    import sys
    env={k:v for k,v in os.environ.items() if not k.startswith(('DJANGO_','AI_','RAM_TEST_','OPENAI_','DEEPSEEK_','QCLAW_','DB_','DATABASE_','PYTHONPATH','PYTHONHOME'))}
    # config.settings.test is source-controlled: only base + literal memory default,
    # no DATABASE_URL, custom router, env loading or external startup hook consumers.
    env.update(DJANGO_SETTINGS_MODULE='config.settings.test',PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    code="import django,json;django.setup();from django.core.management import call_command;from django.db import connection;assert connection.settings_dict['NAME']==':memory:';call_command('migrate',verbosity=0,interactive=False);print(json.dumps(connection.cursor().execute(\"SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name\").fetchall()));connection.close()"
    try:
        result=subprocess.run([sys.executable,'-c',code],cwd=ROOT/'backend',env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
        if result.returncode:raise ValueError('child rejected')
        rows=json.loads(result.stdout)
        if not isinstance(rows,list) or not rows:raise ValueError('invalid schema')
        for row in rows:
            if not isinstance(row,list) or len(row)!=4 or row[0] not in ('table','index','view','trigger') or not all(isinstance(x,str) for x in row[:3]) or row[3] is not None and not isinstance(row[3],str):raise ValueError('invalid schema')
        return [tuple(row) for row in rows]
    except (OSError,subprocess.TimeoutExpired,ValueError,TypeError):
        raise OpsError('REFERENCE_SCHEMA_UNAVAILABLE') from None

def structure(db):
    if db.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise OpsError('INTEGRITY_FAILED')
    if db.execute('PRAGMA foreign_key_check').fetchall():raise OpsError('FOREIGN_KEYS_FAILED')
    schema=db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").fetchall()
    if schema!=_expected_schema():raise OpsError('SCHEMA_MISMATCH')
    tables=[x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name NOT LIKE 'sqlite_%' OR name='sqlite_sequence') ORDER BY name")]
    if 'django_migrations' not in tables or 'rbac_managed_sessions' not in tables or 'rbac_login_windows' not in tables:raise OpsError('SCHEMA_UNSUPPORTED')
    # Exact migration set must match this installed source; old/incompatible backups fail closed.
    from django.db.migrations.loader import MigrationLoader
    expected=set(MigrationLoader(None).disk_migrations)
    actual=set(db.execute('SELECT app,name FROM django_migrations'))
    if expected!=actual:raise OpsError('MIGRATION_SET_MISMATCH')
    return schema,tables

def compare(left,right):
    ls,tables=structure(left);rs,rt=structure(right)
    if ls!=rs or tables!=rt:raise OpsError('SCHEMA_MISMATCH')
    counts={}
    for table in tables:
        quoted='"'+table.replace('"','""')+'"'
        # Internal full-column multiset comparison. Never print rows or content hashes.
        a=left.execute('SELECT * FROM '+quoted).fetchall();b=right.execute('SELECT * FROM '+quoted).fetchall()
        if sorted(a,key=repr)!=sorted(b,key=repr):raise OpsError('DATA_MISMATCH')
        counts[table]=len(a)
    return counts

def backup():
    start=time.monotonic();source=_source()
    with closing(_connect_ro(source)) as src:structure(src)
    base=_base();identity=uuid.uuid4().hex
    folder=base/'backups'/identity;folder.mkdir(mode=0o700);_private(folder,True)
    target=folder/'database.sqlite3'
    # O_EXCL never overwrites, and inherited private ACL protects from creation onward.
    with target.open('xb'):pass
    _private(target)
    try:
        with closing(_connect_ro(source)) as src,closing(sqlite3.connect(target)) as dst:
            src.backup(dst,pages=128,sleep=0.01)
        with closing(_connect_ro(target)) as db:
            _,tables=structure(db)
            counts={t:db.execute('SELECT COUNT(*) FROM "'+t.replace('"','""')+'"').fetchone()[0] for t in tables}
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        manifest={'format':1,'id':identity,'sha256':digest,'sqlite':sqlite3.sqlite_version,'table_counts':counts,'contains_secrets':True}
        meta=folder/'manifest.json';meta.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8');_private(meta)
        return {'ok':True,'backup_id':identity,'table_count':len(tables),'seconds':round(time.monotonic()-start,3),'contains_secrets':True}
    except Exception as error:
        if isinstance(error,OpsError):raise
        raise OpsError('BACKUP_FAILED') from None

def restore(identity):
    start=time.monotonic();identity=_id(identity);base=_base();folder=_unlinked(base/'backups'/identity)
    source=_unlinked(folder/'database.sqlite3');meta=_unlinked(folder/'manifest.json')
    if not source.is_file() or not meta.is_file():raise OpsError('BACKUP_UNAVAILABLE')
    try:manifest=json.loads(meta.read_text(encoding='utf-8'))
    except Exception:raise OpsError('MANIFEST_INVALID') from None
    if manifest.get('id')!=identity or manifest.get('sha256')!=hashlib.sha256(source.read_bytes()).hexdigest():raise OpsError('BACKUP_DIGEST_MISMATCH')
    # Validate source before creating target; path is fixed and absent by contract.
    with closing(_connect_ro(source)) as src:structure(src)
    target_dir=base/'restores'/identity
    _unlinked(target_dir)
    if target_dir.exists():raise OpsError('RESTORE_TARGET_EXISTS')
    target_dir.mkdir(mode=0o700);_private(target_dir,True);target=target_dir/'database.sqlite3'
    with target.open('xb'):pass
    _private(target)
    try:
        with closing(_connect_ro(source)) as src,closing(sqlite3.connect(target)) as dst:src.backup(dst,pages=128,sleep=0.01)
        with closing(_connect_ro(source)) as src,closing(_connect_ro(target)) as dst:counts=compare(src,dst)
        return {'ok':True,'backup_id':identity,'restored_id':identity,'all_columns_equal':True,'migration_metadata_equal':True,'table_count':len(counts),'seconds':round(time.monotonic()-start,3),'not_live_replacement':True}
    except Exception as error:
        if isinstance(error,OpsError):raise
        raise OpsError('RESTORE_FAILED') from None

def health():
    try:
        with closing(_connect_ro(_source())) as db:_,tables=structure(db)
        return {'ok':True,'database_ready':True,'schema_current':True,'table_count':len(tables)}
    except Exception as error:
        return {'ok':False,'database_ready':False,'code':error.code if isinstance(error,OpsError) else 'HEALTH_FAILED'}
