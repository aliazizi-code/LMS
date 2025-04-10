from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404

from accounts.models import EmployeeProfile, SocialLink, UserProfile
from accounts.serializers import (
    GroupSerializer,
    EmployeeDetailSerializer,
)


class GroupListView(APIView):

    def get(self, request):
        queryset = Group.objects.filter(custom_groups__is_display=True)
        serializer = GroupSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeDetailView(APIView):
    serializer_class = EmployeeDetailSerializer

    def get(self, request, username=None):
        queryset = get_object_or_404(
            UserProfile,
            employee_profile__username=username,
            gender__isnull=False,
            age__isnull=False,
            bio__isnull=False,
            job__isnull=False,
            avatar__isnull=False,
            user__first_name__isnull=False,
            user__last_name__isnull=False,
        )
        serializer = self.serializer_class(queryset)
        
        has_social_link = bool(queryset.employee_profile.social_link.all())
        has_groups = bool(queryset.user.groups.filter(custom_groups__is_display=True))
        
        if not has_social_link or not has_groups:
            return Response({},status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
