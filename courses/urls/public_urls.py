from django.urls import path, re_path

from courses.views import (
    UsersCourseListViewSet,
    UserCourseDetailView,
    CategoryHierarchyListView,
)


urlpatterns = [
    path('', UsersCourseListViewSet.as_view({'get': 'list'}), name='course-list'),
    
    path('categories/', CategoryHierarchyListView.as_view(), name='categories-list'),
    
    re_path(r'^(?P<slug>[\w\-آ-ی]+)/?$', UserCourseDetailView.as_view(), name='course-detail'),
]
