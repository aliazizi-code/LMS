from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .forms import UserCreationForm, UserChangeForm
from . import models


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


class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('title',)
    ordering = ('title',)

    fieldsets = (
        (None, {'fields': ('title', 'parent', 'is_active')}),
    )


class JobAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('title',)
    filter_horizontal = ('category',)  # For ManyToMany field
    ordering = ('title',)

    fieldsets = (
        (None, {'fields': ('title', 'category')}),
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
        'fields': ('job', 'age', 'gender')
    }),
    ('عکس پروفایل', {
        'fields': ('avatar', 'thumbnail')
    }),
)
    
    
    def thumbnail(self, obj):
        if obj.avatar:
            return format_html(f'<img src="{obj.avatar.url}" style="width: 70px; height: auto;" />')
        return "No Image"

    thumbnail.short_description = "Thumbnail"


class CustomGroupAdmin(admin.ModelAdmin):
    list_display = ("group", "is_display")


admin.site.register(models.User, UserAdmin)
admin.site.register(models.JobCategory, JobCategoryAdmin)
admin.site.register(models.Job, JobAdmin)
admin.site.register(models.UserProfile, UserProfileAdmin)
admin.site.register(models.EmployeeProfile)
admin.site.register(models.SocialLink)
admin.site.register(models.CustomGroup, CustomGroupAdmin)
