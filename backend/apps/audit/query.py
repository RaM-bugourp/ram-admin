"""One audit query contract for JSON and CSV. No payload or sensitive metadata."""
import csv
import io
from django.utils.dateparse import parse_datetime
from rest_framework.exceptions import ValidationError
from apps.audit.models import OperationLog
from apps.common.inputs import positive_int

FIELDS=('id','actor_id','actor_name','action','resource','object_id','outcome','created_at')
EXPORT_LIMIT=5000
FILTERS={'action','resource','outcome','actor_id','start','end'}

def filtered(params, *, export=False):
    allowed=FILTERS if export else FILTERS|{'page','page_size'}
    for key in params:
        if key not in allowed or len(params.getlist(key))!=1:
            raise ValidationError({key:'不支持或重复的筛选字段'})
    qs=OperationLog.objects.select_related('actor').all()
    for field in ('action','resource','outcome'):
        value=params.get(field,'')
        if len(value)>100:raise ValidationError({field:'筛选过长'})
        if value:qs=qs.filter(**{field:value})
    if params.get('actor_id'):qs=qs.filter(actor_id=positive_int(params['actor_id'],'actor_id'))
    dates={}
    for key,lookup in [('start','created_at__gte'),('end','created_at__lte')]:
        if params.get(key):
            try:value=parse_datetime(params[key])
            except (ValueError,TypeError,OverflowError):value=None
            if value is None or value.tzinfo is None:raise ValidationError({key:'需要有效且带时区的ISO日期时间'})
            dates[key]=value;qs=qs.filter(**{lookup:value})
    if len(dates)==2 and dates['start']>dates['end']:raise ValidationError({'end':'结束时间不能早于开始时间'})
    return qs

def row(item):
    return {'id':item.pk,'actor_id':item.actor_id,'actor_name':item.actor.username if item.actor else '',
            'action':item.action,'resource':item.resource,'object_id':item.object_id,'outcome':item.outcome,'created_at':item.created_at.isoformat()}

def csv_cell(value):
    if value is None:return ''
    text=str(value)
    # Strip line/control injection and neutralize formulas after any leading whitespace.
    text=''.join(' ' if ord(c)<32 or ord(c)==127 else c for c in text)
    if text.lstrip().startswith(('=','+','-','@')):text="'"+text
    return text

def csv_bytes(items):
    buf=io.StringIO(newline='');writer=csv.writer(buf,lineterminator='\r\n');writer.writerow(FIELDS)
    for item in items:
        values=row(item);writer.writerow([csv_cell(values[key]) for key in FIELDS])
    return ('\ufeff'+buf.getvalue()).encode('utf-8')
