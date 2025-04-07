from django.urls import path, re_path

from courses.views import *


course_teacher_methods = {
    
    
}


urlpatterns = [
    path('', CourseListView.as_view({'get': 'list'}), name='course-list'),
    
    path('learning-level/', LearningLevelView.as_view(), name='learning-level'),
    
    
    path(
        'teacher/create/',
        CourseByTeacherViewSet.as_view({'post': 'create'}),
        name='course-teacher-create'
    ),
    path(
        'teacher/list/',
        CourseByTeacherListView.as_view(),
        name='course-teacher-list'
    ),
    path(
        'teacher/season/',
        SeasonView.as_view({'get': 'list', 'post': 'create'}),
        name='course-teacher-season'
    ),
    path(
        'teacher/season/<int:pk>/',
        SeasonView.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='course-teacher-season-detail'
    ),
    re_path(
        r'^teacher/(?P<slug>[\w\-آ-ی]+)/?$',
        CourseByTeacherViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='course-teacher-detail'
    ),
    
    
    path('categories/', CategoryListView.as_view(), name='categories-list'),
    
    re_path(r'^(?P<slug>[\w\-آ-ی]+)/?$', CourseDetailView.as_view(), name='course-detail'),
]
