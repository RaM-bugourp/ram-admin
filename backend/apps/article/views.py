from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Article, Category
from .serializers import (
    ArticleListSerializer, ArticleDetailSerializer,
    ArticleCreateSerializer, CategorySerializer,
)


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.filter(is_deleted=False)
    serializer_class = ArticleListSerializer
    filterset_fields = ['status', 'category', 'created_by']
    search_fields = ['title', 'content', 'tags']
    ordering_fields = ['id', 'created_at', 'view_count']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return ArticleCreateSerializer
        return ArticleListSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete()

    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.status = 'published'
        article.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Published'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        article = self.get_object()
        article.status = 'archived'
        article.save(update_fields=['status', 'updated_at'])
        return Response({'message': 'Archived'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        user = request.user
        queryset = self.get_queryset()
        if not user.is_superuser:
            queryset = queryset.filter(created_by=user)
        total = queryset.count()
        published = queryset.filter(status='published').count()
        draft = queryset.filter(status='draft').count()
        return Response({'total': total, 'published': published, 'draft': draft})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    ordering_fields = ['sort', 'id']
