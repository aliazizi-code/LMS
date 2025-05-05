from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.core.exceptions import ValidationError
from mptt.admin import DraggableMPTTAdmin
from simple_history.admin import SimpleHistoryAdmin

from .models import Comment
from .forms import CommentAdminForm


class CommentAdmin(SimpleHistoryAdmin, DraggableMPTTAdmin):
    form = CommentAdminForm
    list_display = (
        "tree_actions", "indented_title",
        "is_approved", "is_deleted"
    )
    list_filter = ("is_approved", "is_deleted", "created_at", 'user__id')
    search_fields = ("text", "object_slug")
    readonly_fields = (
        "created_at", "updated_at", 'approved_at', 'parent_link',
        'approved_by', 'user', 'object_slug', 'content_type',
        'text'
        )
    ordering = ["tree_id", "lft"]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'text'),
            'classes': ('wide',)
        }),
        ('ارتباط با محتوا', {
            'fields': ('content_type', 'object_slug', 'parent_link'),
        }),
        ('وضعیت تایید', {
            'fields': ('is_approved', 'approved_by'),
            
        }),
        ('زمان', {
            'fields': ('created_at', 'updated_at', 'approved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def parent_link(self, obj):
        if obj.parent:
            url = reverse("admin:comments_comment_change", args=[obj.parent.pk])
            parent_user = obj.parent.user.id if obj.parent.user else "نامشخص"
            return format_html(
                '<a href="{}" target="_self" title="متن: {}">[نظر: {} - کاربر: {}]</a>',
                url,
                obj.parent.text,
                obj.parent.pk,
                parent_user
            )
        return "-"
    parent_link.short_description = "والد"
    
    def indented_title(self, obj):
        default_title = super().indented_title(obj)
        url = reverse("admin:comments_comment_change", args=[obj.pk])
        return format_html(
            '<a href="{}" target="_self" title="{}">{}</a>',
            url,
            obj.text,
            default_title
        )
    indented_title.short_description = "متن نظر"
    
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser and not obj.is_approved:
            raise PermissionError("خطا: شما اجازه تغییر وضعیت به 'عدم تایید' را ندارید.")
        
        obj.approved_by = request.user
        super().save_model(request, obj, form, change)


admin.site.register(Comment, CommentAdmin)
