from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404, get_list_or_404
from django.db.models import Q, Prefetch, Count, F
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from courses.models import Course
from courses.serializers import *
from .filters import CourseFilter
from .permissions import IsTeacher


class CourseListPagination(PageNumberPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100


@method_decorator(cache_page(60 * 15), name='dispatch')
class UsersCourseListViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        categories__is_active=True,
    ).select_related(
        'teacher', 'price', 'learning_path',
    ).prefetch_related(
        'categories', 'tags',
    ).annotate(
        teacher_username=F('teacher__user_profile__employee_profile__username'),
        teacher_first_name=F('teacher__first_name'),
        teacher_last_name=F('teacher__last_name'),
    )
    serializer_class = UsersCourseListSerializer
    pagination_class = CourseListPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter
    

@method_decorator(cache_page(60 * 15), name='dispatch')
class UserCourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(
        is_published=True,
        is_deleted=False,
        categories__is_active=True,
    ).select_related(
        'price',
        'learning_path',
        'learning_path__start_level',
        'learning_path__end_level',
    ).prefetch_related(
        'tags',
        Prefetch(
            'features',
            queryset=Feature.objects.filter(
                course__is_deleted=False
            ).order_by('order', 'created_at', 'id'),
            to_attr='prefetched_features'
        ),
        Prefetch(
            'faqs',
            queryset=FAQ.objects.filter(
                course__is_deleted=False
            ).order_by('order', 'created_at', 'id'),
            to_attr='prefetched_faqs'
        ),
        Prefetch(
            'lessons',
            queryset=Lesson.objects.filter(
                is_deleted=False,
                is_published=True
            ).select_related('season').order_by('order', 'created_at', 'id'),
            to_attr='prefetched_lessons'
        ),
        Prefetch(
            'seasons',
            queryset=Season.objects.filter(
                is_deleted=False,
                is_published=True,
                lessons__is_deleted=False,
                lessons__is_published=True
            ).annotate(
                valid_lessons_count=Count(
                    'lessons',
                    filter=Q(lessons__is_deleted=False, lessons__is_published=True)
                )
            ).filter(valid_lessons_count__gt=0).order_by(
                'order', 'created_at', 'id'
            ).prefetch_related(
                Prefetch(
                    'lessons',
                    queryset=Lesson.objects.filter(
                        is_deleted=False,
                        is_published=True
                    ).select_related('season').order_by('order', 'created_at', 'id'),
                    to_attr='prefetched_lessons'
                )
            ),
            to_attr='prefetched_seasons'
        )
    ).annotate(
        teacher_username=F('teacher__user_profile__employee_profile__username'),
        teacher_first_name=F('teacher__first_name'),
        teacher_last_name=F('teacher__last_name'),
    )
    serializer_class = UserCourseDetailSerializer
    lookup_field = 'slug'


@method_decorator(cache_page(60 * 60), name='dispatch')
class CategoryHierarchyListView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = CourseCategory.objects.filter(parent=None, is_active=True).distinct()
  

class TeacherCoursesListListView(generics.ListAPIView):
    serializer_class = TeacherCoursesSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    pagination_class = CourseListPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter
    
    def get_queryset(self):
        return Course.objects.filter(
            is_deleted=False,
            teacher=self.request.user,
        ).select_related(
            'teacher', 
        ).distinct()


class TeacherCourseDetailManagementViewSet(viewsets.ViewSet):
    serializer_class = TeacherCourseDetailManagementSerializer
    pagination_class = CourseListPagination
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, slug=None):
        queryset = get_object_or_404(
            Course.objects.select_related('teacher'),
            slug=slug,
            teacher=request.user
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, slug=None):
        queryset = get_object_or_404(
            Course.objects.select_related('teacher'),
            slug=slug,
            teacher=request.user
        )
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, slug=None):
        queryset = get_object_or_404(
            Course.objects.select_related('teacher'),
            slug=slug,
            teacher=request.user
        )
        try:
            queryset.is_deleted = True
            queryset.full_clean()
            queryset.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherSeasonManagementViewSet(viewsets.ViewSet):
    serializer_class = TeacherSeasonManagementSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def list(self, request):
        course_slug = request.query_params.get('course_slug')

        if not course_slug:
            return Response({"course_slug": "شناسه دوره ضروری است."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = get_list_or_404(
            Season.objects.select_related(
                'course',
                'course__teacher',
            ),
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
        queryset = get_object_or_404(
            Season.objects.select_related(
                'course',
                'course__teacher',
            ),
            pk=pk,
            course__teacher=request.user,
            is_deleted=False,
        )
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(
            Season.objects.select_related(
                'course',
                'course__teacher',
            ),
            pk=pk,
            course__teacher=request.user,
            is_deleted=False,
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:
                raise serializers.ValidationError({"error": str(e)})
             
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        queryset = get_object_or_404(
            Season.objects.select_related(
                'course',
                'course__teacher',
            ),
            pk=pk,
            course__teacher=request.user,
            is_deleted=False,
        )
        try:
            queryset.is_deleted = True
            queryset.full_clean()
            queryset.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherLessonManagementViewSet(viewsets.ViewSet):
    serializer_class = TeacherLessonManagementSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def list(self, request):
        course_slug = request.query_params.get('course_slug')

        if not course_slug:
            return Response({"course_slug": "شناسه دوره ضروری است."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = get_list_or_404(
            Lesson.objects.select_related(
                'course',
                'course__teacher',
            ),
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
        queryset = get_object_or_404(
            Lesson.objects.select_related(
                'course',
                'course__teacher',
            ),
            pk=pk,
            course__teacher=request.user,
            is_deleted=False,
        )
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(
            Lesson.objects.select_related(
                'course',
                'course__teacher',
            ),
            pk=pk,
            course__teacher=request.user,
            is_deleted=False,
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
            except Exception as e:
                raise serializers.ValidationError({"error": str(e)})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        queryset = get_object_or_404(
            Lesson.objects.select_related(
                'course',
                'course__teacher',
            ),
            pk=pk,
            course__teacher=request.user,
            is_deleted=False,
        )
        try:
            queryset.is_deleted = True
            queryset.full_clean()
            queryset.save()
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except Exception as e:
            raise serializers.ValidationError({"error": str(e)})

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherFeatureViewSet(viewsets.ViewSet):
    serializer_class = TeacherFeatureSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def list(self, request):
        course_slug = request.query_params.get('course_slug')
        if not course_slug:
            return Response({"course_slug": "شناسه دوره ضروری است."}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = get_list_or_404(
            Feature,
            course__slug=course_slug,
            course__teacher=request.user,
        )
        
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(
            Feature.objects.select_related('course__teacher'),
            pk=pk,
            course__teacher=request.user
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        queryset = get_object_or_404(
            Feature.objects.select_related('course__teacher'),
            pk=pk,
            course__teacher=request.user
        )
        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherFAQViewSet(viewsets.ViewSet):
    serializer_class = TeacherFAQSerializer
    permission_classes = [IsAuthenticated, IsTeacher]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def list(self, request):
        course_slug = request.query_params.get('course_slug')
        if not course_slug:
            return Response({"course_slug": "شناسه دوره ضروری است."}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = get_list_or_404(
            FAQ,
            course__slug=course_slug,
            course__teacher=request.user,
        )
        
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(
            FAQ.objects.select_related('course__teacher'),
            pk=pk,
            course__teacher=request.user
        )
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        queryset = get_object_or_404(
            FAQ.objects.select_related('course__teacher'),
            pk=pk,
            course__teacher=request.user
        )
        queryset.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
