from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from . import models


class UserAdmin(UserAdmin):
    list_display = ('phone', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('phone', 'email', 'first_name', 'last_name')
    ordering = ('phone',)

    fieldsets = (
        (None, {'fields': ('phone', 'email', 'first_name', 'last_name', 'is_active', 'is_staff')}),
    )


admin.site.register(models.User, UserAdmin)
admin.site.register(models.UserProfile)