from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from accounts.models import UserProfile, User
from accounts.tasks import send_email_tasks
from utils import generate_otp_change_phone, EmailTokenManager, CacheManager
from accounts.tasks import send_otp_to_phone_tasks
from accounts.serializers import (
    UserProfileSerializer,
    ChangePhoneRequestSerializer,
    ChangePhoneVerifySerializer,
)
from accounts.docs.schema import *


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
                    
            return Response({"detail": "OTP sent successfully."}, status=status.HTTP_200_OK)
        
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
            return Response({"detail": "Number changed successfully."}, status=status.HTTP_200_OK)
             
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






