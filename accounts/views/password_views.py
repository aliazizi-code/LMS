from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.hashers import is_password_usable

from accounts.serializers.password_serializers import (
    BasePasswordSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
)


class SetPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BasePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user
            
            if is_password_usable(user.password):
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
            data = serializer.validated_data
            new_password = data['password']
            
            user.set_password(new_password)
            user.save()

            return Response({}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    serializer_class = ForgotPasswordSerializer
    # permission_classes = [IsAnonymousUser]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            return Response(
                data={'phone': data['phone'],
                      'has_user': True},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
