"""
代码生成器 - 自动生成 CRUD 代码

用法：
    python scripts/codegen.py <app_name> <model_name> [--fields field1:type1,field2:type2]

示例：
    python scripts/codegen.py shop Product --fields name:str,price:decimal,stock:int
"""

import os
import sys
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# 模板定义
MODEL_TEMPLATE = '''
"""
apps/{app_name}/models.py - {model_name} 模型
"""

from django.db import models
from packages.core.foundation.models import BaseAuditModel


class {ModelName}(BaseAuditModel):
    """
    {model_name_cn}模型
    """
{fields}

    class Meta:
        db_table = '{app_name}_{model_name}'
        verbose_name = '{model_name_cn}'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return str(self.id)
'''

SERIALIZER_TEMPLATE = '''
"""
apps/{app_name}/serializers.py - {model_name} 序列化器
"""

from rest_framework import serializers
from .models import {ModelName}


class {ModelName}Serializer(serializers.ModelSerializer):
    """{model_name_cn}序列化器"""

    class Meta:
        model = {ModelName}
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']


class {ModelName}ListSerializer(serializers.ModelSerializer):
    """列表序列化器（字段精简）"""

    class Meta:
        model = {ModelName}
        fields = ['id', {list_fields}]
'''

VIEW_TEMPLATE = '''
"""
apps/{app_name}/views.py - {model_name} 视图
"""

from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

from packages.core.foundation.mixins import AuditOwnerPopulateMixin
from .models import {ModelName}
from .serializers import {ModelName}Serializer, {ModelName}ListSerializer


class {ModelName}ViewSet(AuditOwnerPopulateMixin, viewsets.ModelViewSet):
    """
    {model_name_cn}视图集

    提供：
        GET    /{model_name}s/           列表
        POST   /{model_name}s/           创建
        GET    /{model_name}s/{{id}}/    详情
        PUT    /{model_name}s/{{id}}/    全量更新
        PATCH  /{model_name}s/{{id}}/    部分更新
        DELETE /{model_name}s/{{id}}/    删除（软删除）
    """
    queryset = {ModelName}.objects.all()
    serializer_class = {ModelName}Serializer
    list_serializer_class = {ModelName}ListSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {filter_fields}
    search_fields = {search_fields}
    ordering_fields = ['created_at', 'updated_at']
'''

URL_TEMPLATE = '''
"""
apps/{app_name}/urls.py - {model_name} 路由
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import {ModelName}ViewSet

router = DefaultRouter()
router.register(r'{model_name}s', {ModelName}ViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
'''

APP_TEMPLATE = '''
"""
apps/{app_name}/apps.py
"""

from django.apps import AppConfig


class {AppName}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.{app_name}'
    verbose_name = '{app_name_cn}'
'''

# 字段类型映射
FIELD_TYPES = {
    'str': 'models.CharField(max_length=200, verbose_name="{verbose_name}")',
    'text': 'models.TextField(verbose_name="{verbose_name}")',
    'int': 'models.IntegerField(verbose_name="{verbose_name}")',
    'decimal': 'models.DecimalField(max_digits=10, decimal_places=2, verbose_name="{verbose_name}")',
    'float': 'models.FloatField(verbose_name="{verbose_name}")',
    'bool': 'models.BooleanField(default=False, verbose_name="{verbose_name}")',
    'date': 'models.DateField(verbose_name="{verbose_name}")',
    'datetime': 'models.DateTimeField(verbose_name="{verbose_name}")',
    'fk': 'models.ForeignKey("{related}", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="{verbose_name}")',
    'm2m': 'models.ManyToManyField("{related}", blank=True, verbose_name="{verbose_name}")',
}


def parse_fields(fields_str):
    """解析字段定义"""
    if not fields_str:
        return []

    fields = []
    for field_def in fields_str.split(','):
        parts = field_def.strip().split(':')
        name = parts[0]
        ftype = parts[1] if len(parts) > 1 else 'str'
        related = parts[2] if len(parts) > 2 else ''
        fields.append({
            'name': name,
            'type': ftype,
            'related': related,
            'verbose_name': name.replace('_', ' ').title(),
        })
    return fields


def generate_model_fields(fields):
    """生成模型字段代码"""
    lines = []
    for f in fields:
        template = FIELD_TYPES.get(f['type'], FIELD_TYPES['str'])
        code = template.format(
            verbose_name=f['verbose_name'],
            related=f.get('related', ''),
        )
        lines.append(f"    {f['name']} = {code}")
    return '\n'.join(lines)


def generate_code(app_name, model_name, fields_str=None, model_name_cn=None):
    """生成代码"""
    ModelName = model_name.title().replace('_', '')
    AppName = app_name.title().replace('_', '')
    model_name_cn = model_name_cn or model_name
    app_name_cn = app_name.replace('_', ' ').title()

    fields = parse_fields(fields_str)
    model_fields = generate_model_fields(fields)
    list_fields = ', '.join([f"'{f['name']}'" for f in fields[:5]])  # 列表只显示前5个字段
    filter_fields = [f['name'] for f in fields if f['type'] in ['str', 'int', 'bool']]
    search_fields = [f['name'] for f in fields if f['type'] == 'str']

    # 创建目录
    app_dir = BASE_DIR / 'apps' / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / 'migrations').mkdir(exist_ok=True)
    (app_dir / 'migrations' / '__init__.py').touch()

    # 生成文件
    context = {
        'app_name': app_name,
        'model_name': model_name,
        'ModelName': ModelName,
        'AppName': AppName,
        'model_name_cn': model_name_cn,
        'app_name_cn': app_name_cn,
        'fields': model_fields,
        'list_fields': list_fields,
        'filter_fields': filter_fields,
        'search_fields': search_fields,
    }

    files = {
        'models.py': MODEL_TEMPLATE.format(**context),
        'serializers.py': SERIALIZER_TEMPLATE.format(**context),
        'views.py': VIEW_TEMPLATE.format(**context),
        'urls.py': URL_TEMPLATE.format(**context),
        'apps.py': APP_TEMPLATE.format(**context),
    }

    for filename, content in files.items():
        filepath = app_dir / filename
        if not filepath.exists():
            filepath.write_text(content, encoding='utf-8')
            print(f"✅ 创建: {filepath}")
        else:
            print(f"⚠️  已存在: {filepath}")

    # 创建 __init__.py
    (app_dir / '__init__.py').touch()

    print(f"\n🎉 代码生成完成！")
    print(f"\n下一步：")
    print(f"1. 在 settings.py INSTALLED_APPS 中添加 'apps.{app_name}'")
    print(f"2. 在 urls.py 中添加 path('api/{app_name}/', include('apps.{app_name}.urls'))")
    print(f"3. 运行 python manage.py makemigrations {app_name}")
    print(f"4. 运行 python manage.py migrate")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='代码生成器')
    parser.add_argument('app_name', help='应用名称')
    parser.add_argument('model_name', help='模型名称')
    parser.add_argument('--fields', help='字段定义，格式: name:type,name:type')
    parser.add_argument('--name-cn', help='模型中文名')

    args = parser.parse_args()

    generate_code(args.app_name, args.model_name, args.fields, args.name_cn)
