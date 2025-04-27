from django.urls import path
from courses import views


urlpatterns = [
    path('courses/', views.TeacherCourseListViewSet.as_view({'get': 'list'}), name='course-list'),
    path('course/<int:pk>/', views.TeacherCourseDetailView.as_view(), name='course-detail'),
    
    path('seasons/', views.TeacherSeasonView.as_view(), name='season-list'),
    path('lessons/', views.TeacherLessonView.as_view(), name='lesson-list'),
    path('features/', views.TeacherFeatureView.as_view(), name='feature-list'),
    path('faqs/', views.TeacherFAQView.as_view(), name='faq-list'),
    
    path('upload/', views.TeacherUploadMediaViewSet.as_view({'post': 'create'}), name='teacher-upload'),
    
    # region Course Request
    path(
        'course/request/',
        views.TeacherCourseRequestViewSet.as_view({'post': 'create', 'get': 'list'}),
        name='teacher-course-request'
    ),
    path(
        'course/request/<int:pk>/',
        views.TeacherCourseRequestViewSet.as_view(
            {'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}),
        name='teacher-course-request-detail'
    ),
    path(
        'course/send-request/<int:pk>/',
        views.TeacherCourseRequestViewSet.as_view({'post': 'send_request'}),
        name='teacher-course-send-request'
    ),
    path(
        'course/cancel-request/<int:pk>/',
        views.TeacherCourseRequestViewSet.as_view({'post': 'cancel_request'}),
        name='teacher-course-cancel-request'
    ),
    # endregion
]