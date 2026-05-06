"""
分页器
══════════════════════════════════════════════════════════════════

Django REST Framework 的分页配置。

为什么需要统一分页器？
    —— 避免每个 ViewSet 单独配置
    —— 统一响应格式：{ count, results, next, previous }
    —— 前端表格组件依赖固定的响应格式

两种分页模式：
    1. PageNumberPagination  —— 经典的 page=2 模式（当前使用）
       响应：{ count: 100, next: "http://...?page=3", results: [...] }

    2. LimitOffsetPagination —— offset/limit 模式
       响应：{ count: 100, next: "http://...?offset=20&limit=20", results: [...] }

CursorPagination（游标分页）更适合大数据量，但需要数据库支持。
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    标准分页器 —— 适合大多数业务场景。

    请求示例：
        GET /api/products/?page=1&page_size=20&search=keyword&ordering=-created_at

    响应示例：
        {
            "count": 156,
            "next": "http://127.0.0.1:8000/api/products/?page=2&page_size=20",
            "previous": null,
            "results": [
                { "id": 1, "name": "产品A", "price": 99.00, ... },
                ...
            ]
        }

    常用查询参数：
        page       —— 页码（默认1）
        page_size  —— 每页数量（默认20，上限100）
        search     —— 搜索（DjangoFilterBackend + SearchFilter）
        ordering   —— 排序（-created_at 表示降序）
    """

    # 每页默认条数
    page_size = 20

    # 允许客户端指定的每页最大条数（防止一次查太多数据）
    page_size_query_param = 'page_size'
    max_page_size = 100

    # 前端传来的页码参数名（默认是 page）
    page_query_param = 'page'

    def get_paginated_response(self, data):
        """
        自定义分页响应格式。

        默认格式够用，但如果需要附加元信息（如当前页、总页数），
        可以重写这里。
        """
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
            # 附加元信息，方便前端渲染
            'page': self.page.number,
            'page_size': self.page.paginator.per_page,
            'total_pages': self.page.paginator.num_pages,
        })

    def get_paginated_response_schema(self, schema):
        """
        自动生成 API 文档Schema（Django REST Framework Swagger 插件用）。

        如果你用 drf-spectacular 或 drf-yasg，可以自动生成 OpenAPI 文档。
        """
        return {
            'type': 'object',
            'properties': {
                'count': {
                    'type': 'integer',
                    'description': '总记录数',
                },
                'next': {
                    'type': 'string',
                    'nullable': True,
                    'description': '下一页 URL',
                },
                'previous': {
                    'type': 'string',
                    'nullable': True,
                    'description': '上一页 URL',
                },
                'results': {
                    'type': 'array',
                    'items': schema,
                },
            },
        }
