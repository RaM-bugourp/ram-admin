"""Local DB-backed login protection. Never trust forwarded source headers."""
import math
import uuid
from django.conf import settings
from django.contrib.sessions.models import Session
from django.db import DatabaseError, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.crypto import salted_hmac, constant_time_compare
from apps.common.exceptions import BusinessError
from apps.audit import service as audit
from apps.rbac.models import LoginWindow, User, ManagedSession
from apps.rbac.permissions import effective_user, is_root

WINDOW_SECONDS = 300
ACCOUNT_LIMIT = 8
SOURCE_LIMIT = 40
MAX_WINDOWS = 10000

def unavailable():
    return BusinessError('安全服务暂不可用，请稍后重试', 'SECURITY_UNAVAILABLE', 503)

def _key(kind, value):
    return salted_hmac('ramadmin.login.v1.' + kind, value, secret=settings.SECRET_KEY, algorithm='sha256').hexdigest()

def reserve_login(username, source, *, now=None):
    """Every attempt reserves capacity before hashing; success only releases account slot.

    A first write takes SQLite's writer reservation before reading counters. No check-then-write race.
    Account normalization deliberately groups case variants; source is REMOTE_ADDR only.
    """
    now = now or timezone.now()
    keys = [('account', _key('account', username.strip().casefold()), ACCOUNT_LIMIT),
            ('source', _key('source', str(source or 'unknown')[:128]), SOURCE_LIMIT)]
    try:
        with transaction.atomic():
            # First statement is a write, serializing SQLite contenders including insertions.
            LoginWindow.objects.filter(expires_at__lte=now).delete()
            existing = {key: LoginWindow.objects.filter(pk=key).first() for _,key,_ in keys}
            limited = [existing[key] for _,key,limit in keys if existing[key] and existing[key].attempts >= limit]
            if limited:
                # A blocked source must not allocate a bucket for each new username.
                # Persist at most one anonymous limited event per already-limited bucket/window.
                if any(not row.limited_reported for row in limited):
                    audit.record(None, 'session.login_limited', 'session', outcome='denied')
                    LoginWindow.objects.filter(pk__in=[row.pk for row in limited]).update(limited_reported=True)
                return {'retry_after': max(1,max(math.ceil((row.expires_at-now).total_seconds()) for row in limited))}
            remaining = MAX_WINDOWS - LoginWindow.objects.count()
            if sum(row is None for row in existing.values()) > remaining:
                return {'unavailable': True}
            rows = []
            for kind, key, limit in keys:
                row, _ = LoginWindow.objects.get_or_create(key=key, defaults={
                    'kind': kind, 'attempts': 0,
                    'expires_at': now + timezone.timedelta(seconds=WINDOW_SECONDS)})
                rows.append((row, limit))
            for row, _ in rows:
                LoginWindow.objects.filter(pk=row.pk).update(attempts=F('attempts')+1)
            return {'account_key': keys[0][1]}
    except DatabaseError:
        raise unavailable() from None

def failed_login():
    # Unknown/wrong/inactive are intentionally indistinguishable and anonymous.
    audit.record(None, 'session.login_failed', 'session', outcome='denied')

def complete_login(account_key):
    LoginWindow.objects.filter(pk=account_key).delete()

def _current(actor):
    actor = effective_user(actor)
    if actor is None:
        raise BusinessError('无权执行此操作', 'PERMISSION_DENIED', 403)
    return actor

def _active_sessions(user, *, current_key=None):
    """Include pre-upgrade sessions without duplicating raw keys in our registry.

    Decode only internally; an old password hash is not an active session. No decoded data leaves here.
    Session row locks/transaction protect writes; SQLite mutations start with a write in callers.
    """
    rows = []
    for session in Session.objects.filter(expire_date__gt=timezone.now()).order_by('expire_date'):
        data = session.get_decoded()
        if str(data.get('_auth_user_id')) != str(user.pk):
            continue
        hashes=[user.get_session_auth_hash(),*user.get_session_auth_fallback_hash()]
        if not any(constant_time_compare(data.get('_auth_user_hash', ''), candidate) for candidate in hashes):
            continue
        handle, _ = ManagedSession.objects.get_or_create(session=session, defaults={'user': user})
        if handle.user_id != user.pk:
            raise unavailable()
        rows.append((session, handle))
    return rows

@transaction.atomic
def register_session(user, session_key):
    session = Session.objects.get(pk=session_key)
    ManagedSession.objects.get_or_create(session=session, defaults={'user': user})

@transaction.atomic
def list_sessions(actor, current_key):
    actor = _current(actor)
    # A no-op UPDATE is an explicit SQLite writer reservation for registration/cleanup.
    User.objects.filter(pk=actor.pk).update(is_active=F('is_active'))
    ManagedSession.objects.filter(session__expire_date__lte=timezone.now()).delete()
    return [{'id': str(handle.id), 'created_at': handle.created_at.isoformat(),
             'expires_at': session.expire_date.isoformat(), 'current': session.pk == current_key}
            for session, handle in _active_sessions(actor)]

@transaction.atomic
def revoke_sessions(actor, current_key=None, *, handle=None, others=False, target_id=None):
    actor = _current(actor)
    User.objects.filter(pk=actor.pk).update(is_active=F('is_active'))
    # Re-read *after* taking the write reservation: revoked role cannot win a stale snapshot.
    actor = _current(actor)
    admin = target_id is not None
    if admin:
        if not is_root(actor):
            raise BusinessError('仅当前root可撤销用户全部会话', 'PERMISSION_DENIED', 403)
        target = User.objects.with_deleted().filter(pk=target_id).first()
        if not target:
            raise BusinessError('用户不存在', 'NOT_FOUND', 404)
    else:
        target = actor
    sessions = _active_sessions(target)
    removed = 0
    current_revoked = False
    for session, entry in sessions:
        selected = admin or (others and session.pk != current_key) or (handle is not None and str(entry.pk) == str(handle))
        if not selected:
            continue
        current_revoked |= session.pk == current_key
        session.delete()
        removed += 1
    audit.record(actor, 'session.admin_revoke_all' if admin else 'session.revoke_others' if others else 'session.revoke', 'user' if admin else 'session', target.pk if admin else '')
    return {'revoked': removed, 'current_revoked': current_revoked}
