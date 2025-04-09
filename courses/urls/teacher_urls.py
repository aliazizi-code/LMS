from django.urls import path, re_path

from courses.views import (
    TeacherCourseDetailManagementViewSet,
    TeacherCoursesListListView,
    TeacherLessonManagementViewSet,
    TeacherSeasonManagementViewSet,
)


urlpatterns = [
    path(
        'course/create/',
        TeacherCourseDetailManagementViewSet.as_view({'post': 'create'}),
        name='course-teacher-create'
    ),
    path(
        'course/list/',
        TeacherCoursesListListView.as_view(),
        name='course-teacher-list'
    ),
    path(
        'season/',
        TeacherSeasonManagementViewSet.as_view({'get': 'list', 'post': 'create'}),
        name='course-teacher-season'
    ),
    path(
        'season/<int:pk>/',
        TeacherSeasonManagementViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'delete': 'destroy',
            }),
        name='course-teacher-season-detail'
    ),
    path(
        'lesson/',
        TeacherLessonManagementViewSet.as_view({'post': 'create'}),
        name='course-teacher-lesson'
    ),
    path(
        'lesson/<int:pk>/',
        TeacherLessonManagementViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'delete': 'destroy',
            }),
        name='course-teacher-lesson-detail'
    ),
    re_path(
        r'^course/(?P<slug>[\w\-آ-ی]+)/?$',
        TeacherCourseDetailManagementViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'delete': 'destroy',
            }),
        name='course-teacher-detail'
    ),
]