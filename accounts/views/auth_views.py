from django.conf import settings
from django.middleware.csrf import rotate_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.docs.schema import *
from accounts.decorators import debug_sensitive_ratelimit
from accounts.jwt import set_token_cookies, delete_token_cookies
from accounts.models import User
from accounts.serializers import (
    RequestOTPSerializer,
    VerifyOTPSerializer,
    PhoneLoginSerializer,
)
from accounts.tasks import send_otp_to_phone_tasks
from utils import generate_otp_auth_num, OTP_TIMEOUT


class BaseLoginView(APIView):
    serializer_class = None

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(data=self._handle_login(user, request), status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _handle_login(self, user, request):
        response = Response(status=status.HTTP_200_OK)

        # Set auth cookies
        refresh = RefreshToken.for_user(user)
        set_token_cookies(response, str(refresh.access_token), str(refresh))

        # Rotate CSRF token
        # Django: For security reasons, CSRF tokens are rotated each time a user logs in.
        rotate_token(request)

        return response


@method_decorator(
    debug_sensitive_ratelimit(
        key='ip', rate=f'1/{OTP_TIMEOUT}s', method='POST', block=True), name='dispatch'
    )
class RequestOTPView(APIView):
    serializer_class = RequestOTPSerializer
    # permission_classes = [IsAnonymousUser]

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
        response = self._handle_login(user, request)

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
        response = self._handle_login(user, request)

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
