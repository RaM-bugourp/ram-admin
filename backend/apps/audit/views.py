"""Core read-only audit contract; no AI/provider or arbitrary payload dependence."""
from django.core.paginator import Paginator
from django.utils.dateparse import parse_datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from apps.audit.models import OperationLog
from apps.rbac.permissions import EffectiveAuthenticated,require_permission,PERMISSIONS,permission_codes
from apps.common.inputs import pagination,positive_int

class AuditListView(APIView):
    permission_classes=[EffectiveAuthenticated]
    def get(self,request):
        require_permission(request.user,'audit.read')
        from apps.audit.query import filtered,row
        page,size=pagination(request);qs=filtered(request.query_params)
        paginator=Paginator(qs,size);obj=paginator.get_page(page)
        return Response({'data':[row(x) for x in obj.object_list],'pagination':{'page':obj.number,'page_size':size,'total':paginator.count,'total_pages':paginator.num_pages}})

from rest_framework.negotiation import DefaultContentNegotiation

class AuditExportNegotiation(DefaultContentNegotiation):
    def select_renderer(self,request,renderers,format_suffix=None):
        # Success returns an explicit text/csv HttpResponse; errors remain JSON,
        # including for a client that correctly requests Accept: text/csv.
        return renderers[0],renderers[0].media_type

class AuditExportView(APIView):
    permission_classes=[EffectiveAuthenticated]
    content_negotiation_class=AuditExportNegotiation
    def get(self,request):
        from django.db import transaction
        from django.http import HttpResponse
        from apps.audit import service as audit
        from apps.audit.query import filtered,csv_bytes,EXPORT_LIMIT
        require_permission(request.user,'audit.read')
        with transaction.atomic():
            items=list(filtered(request.query_params,export=True)[:EXPORT_LIMIT+1])
            if len(items)>EXPORT_LIMIT:raise ValidationError({'export':f'最多导出{EXPORT_LIMIT}行，请收窄筛选；未截断导出'})
            body=csv_bytes(items)
            audit.record(request.user,'audit.export','audit')
        response=HttpResponse(body,content_type='text/csv; charset=utf-8')
        response['Content-Disposition']='attachment; filename=operation-audit.csv'
        response['Cache-Control']='no-store'
        response['X-Content-Type-Options']='nosniff'
        return response

class PermissionCatalogView(APIView):
    permission_classes=[EffectiveAuthenticated]
    def get(self,request):
        require_permission(request.user,'roles.read')
        allowed=permission_codes(request.user)
        return Response({'data':[{'code':code,'name':name,'grantable':code in allowed} for code,name in PERMISSIONS.items()]})
