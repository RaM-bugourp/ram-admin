"""
apps/article/serializers.py
"""

from rest_framework import serializers
from .models import Article, Category


class ArticleListSerializer(serializers.ModelSerializer):
    """文章列表序列化器（轻量，用于列表展示）"""
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, default='')
    status_text = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'status', 'status_text',
            'category', 'category_name',
            'tags', 'view_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
        ]


class ArticleDetailSerializer(ArticleListSerializer):
    """
    文章详情序列化器（包含正文）
    ActionSerializerMixin 会自动在 retrieve 时用这个
    """
    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ['content']


class ArticleCreateSerializer(serializers.ModelSerializer):
    """创建文章序列化器"""
    class Meta:
        model = Article
        fields = ['title', 'content', 'status', 'category', 'tags']


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器"""
    parent_name = serializers.CharField(source='parent.name', read_only=True, default='')

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'parent_name', 'sort', 'created_at']
