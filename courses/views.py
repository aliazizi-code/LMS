from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from courses.models import Course
from courses.serializers import *
from .filters import CourseFilter
from .permissions import IsTeacher


class CourseListPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100


class UsersCourseListViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        categories__is_active=True,
    ).distinct()
    serializer_class = UsersCourseListSerializer
    pagination_class = CourseListPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter
    

class UserCourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        categories__is_active=True,
    ).distinct()
    serializer_class = UserCourseDetailSerializer
    lookup_field = 'slug'


class CategoryHierarchyListView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = CourseCategory.objects.filter(parent=None, is_active=True).distinct()
  

class TeacherCoursesListListView(generics.ListAPIView):
    serializer_class = TeacherCoursesSerializer
    permission_classes = [IsTeacher]
    pagination_class = CourseListPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter
    
    def get_queryset(self):
        return Course.objects.filter(
            is_deleted=False,
            teacher=self.request.user,
        ).distinct()


class TeacherCourseDetailManagementViewSet(viewsets.ViewSet):
    serializer_class = TeacherCourseDetailManagementSerializer
    pagination_class = CourseListPagination
    permission_classes = [IsTeacher]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, slug=None):
        queryset = get_object_or_404(Course, slug=slug, teacher=request.user)
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, slug=None):
        queryset = get_object_or_404(Course, slug=slug, teacher=request.user)
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, slug=None):
        queryset = get_object_or_404(Course, teacher=request.user, slug=slug)
        queryset.is_deleted = True
        queryset.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherSeasonManagementViewSet(viewsets.ViewSet):
    serializer_class = TeacherSeasonManagementSerializer
    permission_classes = [IsTeacher]
    
    def list(self, request):
        course_slug = request.query_params.get('course_slug')

        if not course_slug:
            return Response({"detail": "شناسه دوره ضروری است."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = get_list_or_404(
            Season,
            course__slug=course_slug,
            course__teacher=request.user,
            is_deleted=False,
        )

        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        queryset = get_object_or_404(Season, pk=pk, course__teacher=request.user, is_deleted=False)
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(Season, pk=pk, course__teacher=request.user, is_deleted=False)
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        queryset = get_object_or_404(Season, pk=pk, course__teacher=request.user, is_deleted=False)
        queryset.is_deleted = True
        queryset.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherLessonManagementViewSet(viewsets.ViewSet):
    serializer_class = TeacherLessonManagementSerializer
    permission_classes = [IsTeacher]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        queryset = get_object_or_404(Lesson, pk=pk, course__teacher=request.user, is_deleted=False)
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(Lesson, pk=pk, course__teacher=request.user, is_deleted=False)
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        queryset = get_object_or_404(Lesson, pk=pk, course__teacher=request.user, is_deleted=False)
        queryset.is_deleted = True
        queryset.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    