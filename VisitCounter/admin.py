from django.contrib import admin

from .models import ContentVisit


class ContentVisitAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_type__model', 'object_slug', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('object_slug', 'content_type')

    # readonly_fields = [field.name for field in ContentVisit._meta.fields]

    # def has_add_permission(self, request):
    #     return False

    # def has_change_permission(self, request, obj=None):
    #     return False

    # def has_delete_permission(self, request, obj=None):
    #     return False


admin.site.register(ContentVisit, ContentVisitAdmin)
