from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import CursorPagination
from rest_framework.exceptions import NotFound
from django.db.models import Q, Prefetch, Count, F, Exists, OuterRef
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib import messages
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.shortcuts import get_list_or_404, get_object_or_404, redirect
from django.contrib.contenttypes.models import ContentType

from courses.models import Course, CourseCategory, RequestStatusChoices
from courses.serializers import *
from .filters import CourseFilter
from .permissions import IsTeacher
from comments.models import Comment


class CourseListPagination(CursorPagination):
    page_size = 16
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_ordering(self, request, queryset, view):
        if queryset.query.order_by:
            return queryset.query.order_by
        return super().get_ordering(request, queryset, view)


# region General View

# @method_decorator(cache_page(60 * 15), name='dispatch')
class UsersCourseListViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.annotate(
        has_active_category=Exists(
            CourseCategory.objects.filter(
                is_active=True,
                courses=OuterRef('pk')
            )
        )
    ).filter(
        has_active_category=True,
        is_published=True,
        is_deleted=False,
    ).exclude(
        status='CANCELLED'
    ).annotate(
        teacher_username=F('teacher__user_profile__employee_profile__username'),
        teacher_first_name=F('teacher__first_name'),
        teacher_last_name=F('teacher__last_name'),
    ).select_related('price')
    serializer_class = CourseListSerializer
    pagination_class = CourseListPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CourseFilter
    

class UserCourseDetailView(generics.RetrieveAPIView):
    serializer_class = CourseDetailSerializer
    lookup_field = 'slug'
    queryset = Course.objects.annotate(
        has_active_category=Exists(
            CourseCategory.objects.filter(
                is_active=True,
                courses=OuterRef('pk')
            )
        )
    ).filter(
        has_active_category=True,
        is_published=True,
        is_deleted=False,
    ).exclude(
        status='CANCELLED'
    ).select_related(
        'price',
        'learning_path',
        'learning_path__start_level',
        'learning_path__end_level'
    ).prefetch_related(
        'tags',
        Prefetch(
            'features',
            queryset=Feature.objects.filter(is_deleted=False).order_by('order', 'created_at', 'id'),
            to_attr='prefetched_features'
        ),
        Prefetch(
            'faqs',
            queryset=FAQ.objects.filter(is_deleted=False).order_by('order', 'created_at', 'id'),
            to_attr='prefetched_faqs'
        ),
        Prefetch(
            'lessons',
            queryset=Lesson.objects.exclude(
                course__status='UPCOMING'
            ).filter(
                is_deleted=False,
                is_published=True,
            ).select_related('season').order_by('order', 'created_at', 'id'),
            to_attr='prefetched_lessons'
        ),
        Prefetch(
            'seasons',
            queryset=Season.objects.exclude(
                course__status='UPCOMING'
            ).filter(
                is_deleted=False,
                course__has_seasons=True
            ).annotate(
                valid_lessons_count=Count(
                    'lessons',
                    filter=Q(lessons__is_deleted=False, lessons__is_published=True)
                )
            ).filter(valid_lessons_count__gt=0).order_by('order', 'created_at', 'id'),
            to_attr='prefetched_seasons'
        )
    ).annotate(
        teacher_username=F('teacher__user_profile__employee_profile__username'),
        teacher_first_name=F('teacher__first_name'),
        teacher_last_name=F('teacher__last_name'),
    )


# @method_decorator(cache_page(60 * 60), name='dispatch')
class CategoryHierarchyListView(generics.ListAPIView):
    serializer_class = CategoryHierarchySerializer
    queryset = CourseCategory.objects.filter(
        parent=None, is_active=True
    ).prefetch_related(
            Prefetch(
                'children',
                queryset=CourseCategory.objects.filter(is_active=True).order_by('lft'),
                to_attr='prefetched_children'
            )
    ).order_by('lft')


class LearningLevelView(generics.ListAPIView):
    serializer_class = LearningLevelSerializer
    queryset = LearningLevel.objects.filter(is_active=True)

# endregion


# region Teacher Views
class TeacherCourseListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherCourseListSerializer
    pagination_class = CourseListPagination
    
    def get_queryset(self):
        return Course.objects.filter(is_deleted=False, teacher=self.request.user)


class TeacherCourseDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherCourseDetailSerializer
    
    def get_queryset(self):
        return Course.objects.filter(is_deleted=False, teacher=self.request.user)


class TeacherSeasonView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherSeasonSerializer
    
    def get_queryset(self):
        course_slug = self.request.query_params.get("course", None)
        if not course_slug:
            raise NotFound(_("هیچ دوره ای یافت نشد."))
        
        return get_list_or_404(
            Season,
            is_deleted=False,
            course__teacher=self.request.user,
            course__slug=course_slug
        )


class TeacherLessonView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherLessonSerializer
    
    def get_queryset(self):
        course_slug = self.request.query_params.get("course", None)
        if not course_slug:
            raise NotFound(_("هیچ دوره ای یافت نشد."))
        
        return get_list_or_404(
            Lesson,
            is_deleted=False,
            course__teacher=self.request.user,
            course__slug=course_slug
        )


class TeacherFeatureView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherFeatureSerializer
    
    def get_queryset(self):
        course_slug = self.request.query_params.get("course", None)
        if not course_slug:
            raise NotFound(_("هیچ دوره ای یافت نشد."))
        
        return get_list_or_404(
            Feature,
            is_deleted=False,
            course__teacher=self.request.user,
            course__slug=course_slug
        )


class TeacherFAQView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherFAQSerializer
    
    def get_queryset(self):
        course_slug = self.request.query_params.get("course", None)
        if not course_slug:
            raise NotFound(_("هیچ دوره ای یافت نشد."))
        
        return get_list_or_404(
            FAQ,
            is_deleted=False,
            course__teacher=self.request.user,
            course__slug=course_slug
        )


class TeacherUploadMediaViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherUploadMediaSerializer
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 

class TeacherCourseRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = TeacherCourseRequestSerializer
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request':request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        queryset = CourseRequest.objects.filter(teacher=request.user, is_deleted=False)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        queryset = get_object_or_404(CourseRequest, teacher=request.user, pk=pk, is_deleted=False)
        serializer = self.serializer_class(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def send_request(self, request, pk=None):
        queryset = get_object_or_404(CourseRequest, teacher=request.user, pk=pk, is_deleted=False)
        
        check_status = bool(queryset.status in [RequestStatusChoices.DRAFT, RequestStatusChoices.NEED_REVISION])
        if check_status:
            queryset.status = RequestStatusChoices.PENDING
            queryset.save()
            return Response([_("درخواست ارسال شد.")], status=status.HTTP_200_OK)
        return Response([_("امکان ارسال درخواست برای این وضعیت نیست.")], status=status.HTTP_400_BAD_REQUEST)
    
    def cancel_request(self, request, pk=None):
        queryset = get_object_or_404(CourseRequest, teacher=request.user, pk=pk, is_deleted=False)
        
        if queryset.status == RequestStatusChoices.PENDING:
            if queryset.need_revision:
                queryset.status = RequestStatusChoices.NEED_REVISION
            else:
                queryset.status = RequestStatusChoices.DRAFT
            queryset.save()
            return Response([_('درخواست لغو شد.')], status=status.HTTP_200_OK)
        return Response([_("امکان لغو درخواست برای این وضعیت نیست.")], status=status.HTTP_400_BAD_REQUEST)  
    
    def partial_update(self, request, pk=None):
        queryset = get_object_or_404(CourseRequest, teacher=request.user, pk=pk, is_deleted=False)
        serializer = self.serializer_class(queryset, data=request.data, partial=True)
        
        check_status = bool(queryset.status in [RequestStatusChoices.DRAFT, RequestStatusChoices.NEED_REVISION])
        if not check_status:
            error_message = {"error": _("در این وضعیت امکان ویرایش درخواست وجود ندارد.")}
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            try:
                queryset.clean()
                serializer.save()
            except Exception as e:
                raise serializers.ValidationError(str(e))
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        queryset = get_object_or_404(CourseRequest, teacher=request.user, pk=pk, is_deleted=False)
        if queryset.status == RequestStatusChoices.DRAFT:
            queryset.is_deleted = True
            try:
                queryset.save()
            except Exception as e:
                raise serializers.ValidationError(str(e))
            return Response([_("با موفقیت حذف شد.")], status=status.HTTP_204_NO_CONTENT)
        return Response([_("امکان حذف ممکن نیست")], status=status.HTTP_400_BAD_REQUEST)
    
# endregion
