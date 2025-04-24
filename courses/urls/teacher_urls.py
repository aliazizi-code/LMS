from django.urls import path
from courses.views import (
    TeacherCourseListViewSet,
    TeacherCourseDetailView,
    TeacherSeasonView,
    TeacherLessonView,
    TeacherFeatureView,
    TeacherFAQView,
    TeacherUploadMediaViewSet,
    TeacherCourseRequestViewSet,
)


urlpatterns = [
    path('courses/', TeacherCourseListViewSet.as_view({'get': 'list'}), name='course-list'),
    path('course/<int:pk>/', TeacherCourseDetailView.as_view(), name='course-detail'),
    
    path('seasons/', TeacherSeasonView.as_view(), name='season-list'),
    path('lessons/', TeacherLessonView.as_view(), name='lesson-list'),
    path('features/', TeacherFeatureView.as_view(), name='feature-list'),
    path('faqs/', TeacherFAQView.as_view(), name='faq-list'),
    
    path('upload/', TeacherUploadMediaViewSet.as_view({'post': 'create'}), name='teacher-upload'),
    
    # region Course Request
    path(
        'course/request/',
        TeacherCourseRequestViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='teacher-course-request'
    ),
    path(
        'course/request/<int:pk>/',
        TeacherCourseRequestViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='teacher-course-request-detail'
    ),
    path(
        'course/send-request/<int:pk>/',
        TeacherCourseRequestViewSet.as_view({'get': 'send_request'}),
        name='teacher-course-send-request'
    ),
    path(
        'course/cancel-request/<int:pk>/',
        TeacherCourseRequestViewSet.as_view({'get': 'cancel_request'}),
        name='teacher-course-cancel-request'
    ),
    # endregion
]