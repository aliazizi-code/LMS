from django.urls import path, re_path

from courses.views import (
    TeacherCourseDetailManagementViewSet,
    TeacherCoursesListListView,
    TeacherLessonManagementViewSet,
    TeacherSeasonManagementViewSet,
    TeacherFeatureViewSet,
    TeacherFAQViewSet,
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
        TeacherLessonManagementViewSet.as_view({'post': 'create', 'get': 'list'}),
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
    path(
        'feature/',
        TeacherFeatureViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='teacher-feature-create-list'
    ),
    path(
        'feature/<int:pk>/',
        TeacherFeatureViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy',}),
        name='teacher-feature-delete-update'
    ),
    path(
        'faq/',
        TeacherFAQViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='teacher-faq-create-list'
    ),
    path(
        'faq/<int:pk>/',
        TeacherFAQViewSet.as_view({'patch': 'partial_update', 'delete': 'destroy',}),
        name='teacher-faq-delete-update'
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