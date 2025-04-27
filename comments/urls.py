from django.urls import path

from . import views


urlpatterns = [
    path('', views.CommentViewSet.as_view({'get': 'list'}), name='comments'),
    path('create/', views.CommentViewSet.as_view({'post': 'create'}), name='comments'),
]
