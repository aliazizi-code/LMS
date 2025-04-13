from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from accounts.models import EmployeeProfile
from accounts.serializers import (
    TeamSerializer,
    EmployeeDetailSerializer,
)


class TeamListView(APIView):
    serializer_class = TeamSerializer

    def get(self, request):
        queryset = EmployeeProfile.objects.filter_completed_profiles()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmployeeDetailView(APIView):
    serializer_class = EmployeeDetailSerializer

    def get(self, request, username=None):
        queryset = EmployeeProfile.objects.filter_completed_profiles().filter(username=username).first()
        
        if queryset is None:
            return Response({"خطا": "پروفایل کارمندی یافت نشد"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.serializer_class(queryset)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
