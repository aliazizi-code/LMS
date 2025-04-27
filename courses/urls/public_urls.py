from django.urls import path, re_path

from courses.views import (
    UsersCourseListViewSet,
    UserCourseDetailView,
    CategoryHierarchyListView,
    LearningLevelView,
)


urlpatterns = [
    path('categories/', CategoryHierarchyListView.as_view(), name='categories-list'),
    path('learning-level/', LearningLevelView.as_view(), name='learning-level-list'),
    
    path('', UsersCourseListViewSet.as_view({'get': 'list'}), name='course-list'),
    re_path(r'^(?P<slug>[\w\-آ-ی]+)/?$', UserCourseDetailView.as_view(), name='course-detail'),
]
