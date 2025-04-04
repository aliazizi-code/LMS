from rest_framework import viewsets, generics
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from courses.models import Course
from courses.serializers import *
from .filters import CourseFilter


class CourseListPagination(PageNumberPagination):
    page_size = 16
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
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter
    

class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        category__is_active=True,
    ).distinct()
    serializer_class = CourseDetailSerializer
    lookup_field = 'slug'


class CategoryListView(generics.ListAPIView):
    serializer_class = CategoryWithChildrenSerializer
    queryset = CourseCategory.objects.filter(parent=None, is_active=True).distinct()
            
