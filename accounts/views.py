# Django Imports
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.middleware.csrf import rotate_token

# Third Party Imports
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.views import TokenRefreshView

# Local Application Imports
from accounts.models import UserProfile, EmployeeProfile, SocialLink, User
from accounts.docs.schema import *
from accounts.serializers import *
from accounts.throttles import DualThrottle
from accounts.permissions import IsEmployeeForProfile, IsAnonymous
from accounts.jwt import set_token_cookies, delete_token_cookies
from accounts.tasks import send_otp_to_phone_tasks
from utils import generate_otp_change_phone, generate_otp_auth_num, generate_otp_reset_password




# region Auth

class BaseLoginView(APIView):
    serializer_class = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(data=self._handle_login(user, request), status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _handle_login(self, user, request, created):
        response = Response(
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

        # Set auth cookies
        refresh = RefreshToken.for_user(user)
        set_token_cookies(response, str(refresh.access_token), str(refresh))

        # Rotate CSRF token
        # Django: For security reasons, CSRF tokens are rotated each time a user logs in.
        rotate_token(request)

        return response


class RequestOTPView(APIView):
    serializer_class = RequestOTPSerializer
    permission_classes = [IsAnonymous]
    throttle_classes = [DualThrottle]

    @request_otp_docs
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            phone = data['phone']
            created = User.objects.filter(phone=phone).exists()

            otp = generate_otp_auth_num(phone)
            send_otp_to_phone_tasks.delay(otp)
            
            data = {'created': not created,}
            
            if settings.DEBUG:
                data['otp'] = otp

            return Response(
                data=data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(BaseLoginView):
    serializer_class = VerifyOTPSerializer

    @verify_otp_docs
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            user, created = User.objects.get_or_create(phone=data['phone'])

            user.last_login = timezone.now()
            user.save()

            return self._generate_response(user, created, request)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_response(self, user, created, request):
        response = self._handle_login(user, request, created)

        response.data = {
            'message': 'User verified successfully',
            'created': created,
            'phone': str(user.phone),
            'full_name': user.full_name(),
        }

        return response


class PhoneLoginView(BaseLoginView):
    serializer_class = PhoneLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            user = serializer.get_user(data)

            return self._generate_response(user, request)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _generate_response(self, user, request):
        response = self._handle_login(user, request, False)

        response.data = {'phone': str(user.phone),}

        return response


class LogoutAPIView(APIView):
    serializer_class = TokenBlacklistSerializer
    permission_classes = (IsAuthenticated,)

    @logout_docs
    def post(self, request):
        serializer = self.serializer_class(data={"refresh": self.get_refresh_token_from_cookie(request)})

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        response = Response({}, status=status.HTTP_200_OK)

        # Delete jwt cookies
        delete_token_cookies(response)

        return response

    def get_refresh_token_from_cookie(self, request) -> Token:
        refresh = self.request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE_REFRESH"])
        if not refresh:
            raise PermissionDenied

        return refresh


class RefreshTokenAPIView(TokenRefreshView):
    @refresh_token_docs
    def post(self, request: Request, *args, **kwargs) -> Response:
        try:
            serializer = self.get_serializer(data={"refresh": self.get_refresh_token_from_cookie()})
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e

        response = Response({
            "success": True,
            "message": "Tokens have been successfully refreshed."},
            status=status.HTTP_200_OK)

        # Set auth cookies
        access_token = serializer.validated_data.get("access")
        refresh_token = serializer.validated_data.get("refresh")
        set_token_cookies(response, access_token, refresh_token)

        return response

    def get_refresh_token_from_cookie(self) -> Token:
        refresh = self.request.COOKIES.get("refresh_token")
        if not refresh:
            raise PermissionDenied

        return refresh

# endregion


# region Employee and Team

# @method_decorator(cache_page(60 * 60), name='dispatch')
class EmployeeListView(APIView):
    serializer_class = EmployeeListSerializer

    def get(self, request):
        queryset = EmployeeProfile.objects.filter_completed_profiles()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# @method_decorator(cache_page(60 * 60), name='dispatch')
class EmployeeDetailView(APIView):
    serializer_class = EmployeeDetailSerializer

    def get(self, request, username=None):
        queryset = EmployeeProfile.objects.filter_completed_profiles().filter(username=username).first()
        
        if queryset is None:
            return Response({"خطا": "پروفایل کارمندی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(queryset)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


# endregion


# region Password

class SetPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BasePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            if bool(user.password):
                return Response(
                    {"detail": "کاربر از قبل رمز عبور دارد. لطفاً از گزینه «تغییر رمز عبور» استفاده کنید."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            password = serializer.validated_data['password']
            user.set_password(password)
            user.save()
            return Response({"detail": "Password set successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        user = request.user

        if serializer.is_valid():
            if not bool(user.password):
                return Response(
                    {"detail": "کاربر رمز عبور ندارد."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            new_password = data['password']
            
            user.set_password(new_password)
            user.save()

            return Response({}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckPhoneView(APIView):
    permission_classes = [IsAnonymous]
    serializer_class = CheckPhoneSerializer

    def get(self, request): 
        serializer = self.serializer_class(data=request.query_params)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            "phone": serializer.validated_data['phone'] 
        }, status=status.HTTP_200_OK)
    

class ResetPasswordView(APIView):

    def get(self, request):
        serializer = CheckPhoneSerializer(data=request.query_params)

        if serializer.is_valid():
            data = serializer.validated_data
            phone = data['phone']
            otp = generate_otp_reset_password(phone)
            send_otp_to_phone_tasks.delay(otp)

            if settings.DEBUG:
                data['otp'] = otp
            
            return Response(
                data=data,
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            user = data['user']
            password = data['password']
            user.set_password(password)
            user.save()

            return Response({}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# endregion


# region Update

@user_profile_viewset_docs
class UserProfileViewSet(viewsets.ViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated] 

    def retrieve(self, request):
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.serializer_class(user_profile)
        return Response(data=serializer.data)
    
    def partial_update(self, request):
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.serializer_class(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePhoneRequestView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePhoneRequestSerializer

    @change_phone_request_docs
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            
            otp = generate_otp_change_phone(data['phone'])
            send_otp_to_phone_tasks.delay(otp)
            
            data = {}
            
            if settings.DEBUG:
                data['otp'] = otp
                    
            return Response(data=data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePhoneVerifyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePhoneVerifySerializer

    @change_phone_verify_docs
    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if serializer.is_valid():
            data = serializer.validated_data
            
            user.phone = data["phone"]
            user.save()
            return Response({"detail": _("شماره با موفقیت تغییر یافت.")}, status=status.HTTP_200_OK)
             
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EmployeeProfileViewSet(viewsets.ViewSet):
    serializer_class = EmployeeProfileSerializer
    permission_classes = [IsAuthenticated, IsEmployeeForProfile] 

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def partial_update(self, request):
        queryset = get_object_or_404(
            EmployeeProfile,
            user_profile__user=request.user,
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request):
        queryset = queryset = get_object_or_404(
            EmployeeProfile.objects.only('username'),
            user_profile__user=request.user,
        )
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeSocialLinkViewSet(viewsets.ViewSet):
    serializer_class = EmployeeSocialLinkSerializer
    permission_classes = [IsAuthenticated, IsEmployeeForProfile]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request):
        social_media_type = request.data.get('social_media_type')
        if not social_media_type:
            return Response({"social_media_type": "این فیلد الزامی است."}, status=status.HTTP_400_BAD_REQUEST)
        queryset = get_object_or_404(
            SocialLink.objects.select_related(
                'employee_profile__user_profile__user'    
            ).only(
                'id', 'employee_profile__user_profile__user__id'    
            ),
            employee_profile__user_profile__user=request.user,
            social_media_type=social_media_type
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        queryset = SocialLink.objects.select_related(
            'employee_profile__user_profile__user',
        ).only(
            'id',
            'social_media_type',
            'employee_profile__user_profile__user__id',
        ).filter(
            employee_profile__user_profile__user=request.user
        )
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# @method_decorator(cache_page(60 * 60), name='dispatch')
class SkillListView(generics.ListAPIView):
    serializer_class = SkillListSerializer
    queryset = Skill.objects.filter(is_active=True)
  

# @method_decorator(cache_page(60 * 60), name='dispatch')
class JobListView(generics.ListAPIView):
    serializer_class = JobListSerializer
    queryset = Job.objects.filter(is_active=True)

# endregion
