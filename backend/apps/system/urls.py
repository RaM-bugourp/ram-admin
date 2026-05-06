from django.urls import path
from . import views

urlpatterns = [
    path('menu/tree/', views.menu_tree, name='menu-tree'),
    path('health/', views.health_check, name='health'),
    path('metrics/', views.metrics, name='metrics'),
]
