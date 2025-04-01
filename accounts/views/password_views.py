from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
            password = serializer.validated_data['password']
            user.set_password(password)
            user.save()
            return Response({"detail": "Password set successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        user = request.user

        if serializer.is_valid():
            data = serializer.validated_data
            old_password = data['old_password']
            new_password = data['password']

            if user.check_password(old_password):
                user.set_password(new_password)
                user.save()

                return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)

            return Response({"detail": "Invalid password."}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            return Response(data={'phone': data['phone']}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
