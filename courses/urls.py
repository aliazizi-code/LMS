from django.urls import path, re_path

from courses.views import *

urlpatterns = [
    path('', CourseListView.as_view({'get': 'list'}), name='course-list'),
    path('categories/', CategoryListView.as_view(), name='categories-list'),
    re_path(r'^categories/(?P<slug>[\w\-آ-ی]+)/?$', CategoryListView.as_view(), name='category_children'),
    re_path(r'^(?P<slug>[\w\-آ-ی]+)/?$', CourseDetailView.as_view(), name='course-detail')
]
