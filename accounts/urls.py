from django.urls import path

from . import views

urlpatterns = [
    # region Authentication endpoints
    path('auth/otp/request/', views.RequestOTPView.as_view(), name='request-otp'),
    path('auth/otp/verify/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/login/phone/', views.PhoneLoginView.as_view(), name='phone-login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    # endregion

    # region Token management
    path('token/refresh/', views.RefreshTokenAPIView.as_view(), name='token_refresh'),
    # endregion

    # region User profile management
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
    path('user/phone/change/verify/', views.ChangePhoneVerifyView.as_view(), name='change-phone-verify'),
    # endregion

    # region Employee management
    path(
        'employee/profile/',
        views.EmployeeProfileViewSet.as_view(
            {
                'get': 'retrieve',
                'patch': 'partial_update',
                'post': 'create',
            }),
        name='employee-profile'
    ),
    path(
        'employee/social-link/',
        views.EmployeeSocialLinkViewSet.as_view(
            {
                'get': 'list',
                'patch': 'partial_update',
                'post': 'create',
            }),
        name='employee-social-link'
    ),
    path('employees/', views.EmployeeListView.as_view(), name='employee-list'),
    path('employee/<str:username>/', views.EmployeeDetailView.as_view(), name='employee-detail'),
    # endregion

    # region Password management
    path('password/check-phone/', views.CheckPhoneView.as_view(), name='check-phone'),
    path('password/reset/request/', views.ResetPasswordView.as_view(), name='reset-password-request'),
    path('password/reset/verify/', views.ResetPasswordView.as_view(), name='reset-password-verify'),
    path('password/change/', views.ChangePasswordView.as_view(), name='change-password'),
    path('password/set/', views.SetPasswordView.as_view(), name='set-password'),
    # endregion
]
