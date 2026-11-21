from apps.audit.models import OperationLog

def record(actor,action,resource,object_id='',outcome='success'):
    # Never accept arbitrary metadata; safe bounded identifiers only.
    return OperationLog.objects.create(actor=actor,action=action,resource=resource,object_id=str(object_id),outcome=outcome)
