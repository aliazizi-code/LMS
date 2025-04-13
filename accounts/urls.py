from django.urls import path

from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/otp/request/', views.RequestOTPView.as_view(), name='request-otp'),
    path('auth/otp/verify/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/login/phone/', views.PhoneLoginView.as_view(), name='phone-login'),

    # Token management
    path('auth/token/refresh/', views.RefreshTokenAPIView.as_view(), name='token_refresh'),

    # User profile management
    path(
        'user/profile/',
        views.UserProfileViewSet.as_view(
        {
            'get': 'retrieve',
            'patch': 'partial_update',
        }),
        name='user-profile'
    ),
    path(
        'user/phone/change/request/',
        views.ChangePhoneRequestView.as_view(),
        name='change-phone-request'
    ),
    path(
        'user/employee/profile/',
        views.EmployeeProfileViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'post': 'create',
            }),
        name='employee-profile'
    ),
    path(
        'user/employee/social-link/',
        views.EmployeeSocialLinkViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'post': 'create',
            }),
        name='employee-social-link'
    ),
    path('employee/<str:username>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    path('user/employee/social-links/', views.EmployeeSocialLinkViewSet.as_view({'get': 'list'}), name='employee-social-links-list'),
    path('user/phone/change/verify/', views.ChangePhoneVerifyView.as_view(), name='change-phone-verify'),
    path('team/', views.TeamListView.as_view(), name='group-list'),

    # Password management
    path('password/reset/', views.ForgotPasswordView.as_view(), name='forgot-password-request'),
    path('password/change/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password/set/', views.SetPasswordView.as_view(), name='set-password'),
]
