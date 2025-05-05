from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.pagination import CursorPagination
from django.core.exceptions import ValidationError
from django.db.models import Prefetch, Case, When, IntegerField, Value, Exists, OuterRef, Q
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property
from django.contrib.contenttypes.models import ContentType

from .serializers import *
from .models import Comment


class CommentListPagination(CursorPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_ordering(self, request, queryset, view):
        if queryset.query.order_by:
            return queryset.query.order_by
        return super().get_ordering(request, queryset, view)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    pagination_class = CommentListPagination
    
    @cached_property
    def content_type(self):
        model_type = self.kwargs.get('type')
        if not model_type:
            raise ValidationError(_("پارامترها الزامی هستند."))
        try:
            return ContentType.objects.get(model=model_type)
        except ContentType.DoesNotExist:
            raise ValidationError(_("مدل یافت نشد."))
    
    def get_queryset(self):
        object_slug = self.kwargs.get('slug')
        
        if not object_slug:
            raise ValidationError(_("پارامترها الزامی هستند."))
        
        model_class = self.content_type.model_class()
        
        parent_object = model_class.objects.filter(
            slug=object_slug,
            is_published=True,
            is_deleted=False,
        ).exists()

        if not parent_object:
            raise ValidationError(_("این آیتم حذف شده یا منتشر نشده است.")) 
        
        base_queryset = Comment.objects.filter(
            content_type=self.content_type,
            object_slug=object_slug,
            is_approved=True,
            is_deleted=False,
        ).select_related('user__user_profile')
        
        top_queryset = base_queryset.filter(parent=None)
        replies_queryset = base_queryset.exclude(parent=None)
        
        
        if self.request.user.is_authenticated:
            top_queryset = top_queryset.annotate(
                replied_by_user=Exists(
                    Comment.objects.filter(
                        parent=OuterRef('pk'),
                        user=self.request.user
                    )
                )
            ).annotate(
                user_priority=Case(
                    When(Q(user=self.request.user) | Q(replied_by_user=True), then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-user_priority', '-created_at')
            
            replies_queryset = replies_queryset.annotate(
                user_priority=Case(
                    When(user=self.request.user, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('-user_priority', '-created_at')
        else:
            top_queryset = top_queryset.order_by('-created_at')
            replies_queryset = replies_queryset.order_by('-created_at')
        
         
        top_queryset = top_queryset.prefetch_related(
            Prefetch(
                'replies',
                queryset=replies_queryset,
                to_attr='prefetched_replies'
            )
        )
        
        return top_queryset

    def destroy(self, request, *args, **kwargs):
        object_id = kwargs.get('pk')
        
        if not request.user.is_authenticated:
            raise NotAuthenticated((_("اطلاعات برای اعتبارسنجی ارسال نشده است.")))
        
        if not object_id:
            return Response({"error": "پارامترها الزامی هستند."}, status=status.HTTP_400_BAD_REQUEST)

        comment = get_object_or_404(
            Comment,
            user=request.user,
            pk=object_id,
            is_deleted=False,
            is_approved=True,
        )

        comment.is_deleted = True
        comment.save()
        return Response({"message": "کامنت با موفقیت حذف شد."}, status=status.HTTP_204_NO_CONTENT)
