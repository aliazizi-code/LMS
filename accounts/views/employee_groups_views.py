from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404

from accounts.models import EmployeeProfile, SocialLink, UserProfile
from accounts.serializers import (
    GroupSerializer,
    EmployeeProfileSerializer,
    UserProfileSerializer,
    EmployeeSocialLinkSerializer,
)


class GroupListView(APIView):

    def get(self, request):
        groups = Group.objects.filter(custom_groups__is_display=True)
        serializer = GroupSerializer(groups, many=True)
        return Response({
            "groups": serializer.data
        }, status=status.HTTP_200_OK)


class EmployeeDetailView(APIView):

    def get(self, request, username=None):
        employee_profile = get_object_or_404(
            EmployeeProfile.objects.prefetch_related('user_profile__user__groups'),
            username=username
        )
        social_links = SocialLink.objects.filter(employee_profile=employee_profile)
        user_profile = employee_profile.user_profile
        
        groups = user_profile.user.groups.filter(custom_groups__is_display=True)
        print(groups)
        
        return Response({
            "group": [group.name for group in groups],
            "employee_profile": EmployeeProfileSerializer(employee_profile).data,
            "social_links": EmployeeSocialLinkSerializer(social_links, many=True).data,
            "user_profile": UserProfileSerializer(user_profile).data
        }, status=status.HTTP_200_OK)
