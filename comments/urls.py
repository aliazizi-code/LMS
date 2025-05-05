from django.urls import re_path, path

from . import views


urlpatterns = [
    path(
        'create/',
        views.CommentViewSet.as_view({'post': 'create'}),
        name='comments-create'
    ),
    path(
        'delete/<int:pk>/',
        views.CommentViewSet.as_view({'delete': 'destroy'}),
        name='comments-create'
    ),
    re_path(
        r'^(?P<type>[\w\-]+)/(?P<slug>[\w\-\u0600-\u06FF]+)/?$',
        views.CommentViewSet.as_view({'get': 'list'}),
        name='comments-list'
    ),
]
