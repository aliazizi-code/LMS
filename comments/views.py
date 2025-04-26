from rest_framework import generics, status, viewsets, mixins
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
        model_type = self.request.query_params.get('type')
        if not model_type:
            raise ValidationError(_("پارامترها الزامی هستند."))
        try:
            return ContentType.objects.get(model=model_type)
        except ContentType.DoesNotExist:
            raise ValidationError(_("مدل یافت نشد."))
    
    def get_queryset(self):
        object_slug = str(self.request.query_params.get('slug'))
        if not object_slug:
            raise ValidationError(_("پارامترها الزامی هستند."))
        
        base_queryset = Comment.objects.filter(
            content_type=self.content_type,
            object_slug=object_slug,
            is_approved=True,
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
