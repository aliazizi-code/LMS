from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts.models import UserProfile, EmployeeProfile, SocialLink
from utils import generate_otp_change_phone
from accounts.docs.schema import *
from accounts.tasks import send_otp_to_phone_tasks
from accounts.permissions import IsEmployeeForProfile
from accounts.serializers import (
    UserProfileSerializer,
    ChangePhoneRequestSerializer,
    ChangePhoneVerifySerializer,
    EmployeeProfileSerializer,
    EmployeeSocialLinkSerializer,
)


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
        queryset = get_object_or_404(EmployeeProfile, user_profile__user=request.user)
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request):
        queryset = get_object_or_404(EmployeeProfile, user_profile__user=request.user)
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
            SocialLink,
            employee_profile__user=request.user,
            social_media_type=social_media_type
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request):
        queryset = get_object_or_404(SocialLink, employee_profile__user=request.user)
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request):
        queryset = SocialLink.objects.filter(employee_profile__user=request.user)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
