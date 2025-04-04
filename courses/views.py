from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from courses.models import Course
from courses.serializers import *


class CourseListPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100
    

class CategoryListPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class CourseListView(viewsets.ModelViewSet):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        category__is_active=True,
    ).distinct()
    serializer_class = CourseListSerializer
    pagination_class = CourseListPagination
    # filter_backends = (DjangoFilterBackend,)
    # filterset_class = EventFilter
    

class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        category__is_active=True,
    ).distinct()
    serializer_class = CourseDetailSerializer
    lookup_field = 'slug'


class CategoryListView(generics.ListAPIView):
    serializer_class = CategoryListSerializer
    pagination_class = CategoryListPagination
    lookup_field = 'slug'
    
    def get_queryset(self):
        slug = self.kwargs.get(self.lookup_field)
        if slug:
            return CourseCategory.objects.filter(parent__slug=slug, is_active=True)
        return CourseCategory.objects.filter(parent=None, is_active=True)
            
