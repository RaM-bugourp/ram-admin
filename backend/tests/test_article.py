"""
文章 CRUD 测试
"""

import pytest


@pytest.mark.django_db
class TestArticleList:
    """文章列表测试"""

    def test_list_articles(self, authenticated_client):
        """测试获取文章列表"""
        response = authenticated_client.get('/api/article/articles/')
        assert response.status_code == 200

    def test_list_articles_pagination(self, authenticated_client):
        """测试分页"""
        response = authenticated_client.get('/api/article/articles/?page=1&page_size=10')
        assert response.status_code == 200


@pytest.mark.django_db
class TestArticleCreate:
    """文章创建测试"""

    def test_create_article(self, authenticated_client):
        """测试创建文章"""
        response = authenticated_client.post('/api/article/articles/', {
            'title': '测试文章',
            'content': '这是测试内容',
            'status': 'draft',
        })
        assert response.status_code == 201

    def test_create_article_without_title(self, authenticated_client):
        """测试缺少标题"""
        response = authenticated_client.post('/api/article/articles/', {
            'content': '没有标题的文章',
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestArticleUpdate:
    """文章更新测试"""

    def test_update_article(self, authenticated_client):
        """测试更新文章"""
        # 先创建
        create_response = authenticated_client.post('/api/article/articles/', {
            'title': '原始标题',
            'content': '原始内容',
            'status': 'draft',
        })
        article_id = create_response.data['id']

        # 再更新
        update_response = authenticated_client.patch(f'/api/article/articles/{article_id}/', {
            'title': '更新后的标题',
        })
        assert update_response.status_code == 200
        assert update_response.data['title'] == '更新后的标题'


@pytest.mark.django_db
class TestArticleDelete:
    """文章删除测试"""

    def test_delete_article(self, authenticated_client):
        """测试删除文章（软删除）"""
        # 先创建
        create_response = authenticated_client.post('/api/article/articles/', {
            'title': '待删除文章',
            'content': '待删除内容',
            'status': 'draft',
        })
        article_id = create_response.data['id']

        # 再删除
        delete_response = authenticated_client.delete(f'/api/article/articles/{article_id}/')
        assert delete_response.status_code == 204

        # 验证软删除（列表中不再显示）
        list_response = authenticated_client.get('/api/article/articles/')
        article_ids = [a['id'] for a in list_response.data['results']]
        assert article_id not in article_ids
