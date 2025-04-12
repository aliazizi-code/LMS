from django.urls import path
from . import views



urlpatterns = [
    path('public/articles/', views.PublicArticleViewSet.as_view({'get': 'list'}), name='public-articles-list'),
    path('public/articles/<slug:slug>/', views.PublicArticleViewSet.as_view({'get': 'retrieve'}), name='public-articles-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
]