from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Group
from .forms import UserCreationForm, UserChangeForm
from . import models
from mptt.admin import DraggableMPTTAdmin


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ('phone', 'is_admin', 'first_name', 'last_name')
    list_filter = ('is_admin',)
    readonly_fields = ('last_login',)

    fieldsets = (
        ('Main', {'fields': ('email', 'phone', 'first_name', 'last_name', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_admin', 'is_staff', 'is_superuser', 'last_login', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {'fields': ('phone', 'email', 'first_name', 'last_name', 'password1', 'password2')}),
    )

    search_fields = ('email', 'phone', 'first_name', 'last_name')
    ordering = ('created_at',)
    filter_horizontal = ('groups', 'user_permissions')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            form.base_fields['is_superuser'].disabled = True
        return form


class JobCategoryAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions",'indented_title', 'is_active')
    autocomplete_fields = ('parent',)
    list_filter = ('is_active', 'parent')
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('title',)

    fieldsets = (
        (None, {'fields': ('title', 'parent', 'is_active', 'created_at', 'updated_at')}),
    )


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'age', 'gender', 'thumbnail')
    readonly_fields = ('thumbnail',)
    list_filter = ('gender', 'job')
    search_fields = ('user__phone', 'user__first_name', 'user__last_name')
    ordering = ('-id',)
    list_per_page = 50

    fieldsets = (
    ('اطلاعات کاربر', {
        'fields': ('user', 'bio')
    }),
    ('اطلاعات شغلی', {
        'fields': ('job', 'age', 'gender', 'skills')
    }),
    ('عکس پروفایل', {
        'fields': ('avatar', 'thumbnail',)
    }),
)
    
    
    def thumbnail(self, obj):
        if obj.avatar:
            return format_html(f'<img src="{obj.avatar.url}" style="width: 70px; height: auto;" />')
        return "No Image"

    thumbnail.short_description = "Thumbnail"


class GroupCustomInline(admin.StackedInline):
    model = models.CustomGroup
    can_delete = False


class GroupAdmin(admin.ModelAdmin):
    inlines = (GroupCustomInline,)
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)


class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('username',)
    search_fields = ('username',)


admin.site.register(models.User, UserAdmin)
admin.site.register(models.JobCategory, JobCategoryAdmin)
admin.site.register(models.Job)
admin.site.register(models.Skill)
admin.site.register(models.UserProfile, UserProfileAdmin)
admin.site.register(models.EmployeeProfile, EmployeeProfileAdmin)
admin.site.register(models.SocialLink)


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)

